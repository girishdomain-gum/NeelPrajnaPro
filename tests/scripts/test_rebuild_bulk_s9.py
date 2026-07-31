"""ARCH-009 §1 — rebuild_bulk: every verdict_trades.* regenerates byte-identically.

Loaded from file (scripts/ is not a package) so the tool logic is the single
source of truth for both the CLI and these tests. These are integration tests: they
operate on the real journal + real (gitignored, reproducible) bulk root, exactly as
the sprint AC demands ("prove it on all three lineages on a clean main").
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from qrf.kernel.records.bulk import BulkStore, _sha256_file
from qrf.kernel.records.store import RecordStore

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def rebuild_bulk():
    return _load("rebuild_bulk")


def _recorded_shas(mod) -> dict[str, str]:
    """{manifest_ref: recorded file_sha256} for every verdict's trades_manifest."""
    store = RecordStore(mod.JOURNAL)
    out: dict[str, str] = {}
    for v in store.query(record_type="verdict"):
        ref = v.payload.get("trades_manifest")
        if ref:
            out[ref] = store.get(ref).payload["file_sha256"]
    return out


def test_rebuild_all_matches_recorded_manifests(rebuild_bulk):
    """Every anchored verdict_trades.* rebuilds to its manifest's exact sha256."""
    recorded = _recorded_shas(rebuild_bulk)
    # h001/h002/h003 (single-window 2024) + h004 (multi-window 2024+2025 union, S9-2)
    # + h007 (NP-ADR-008 §5 v1.1 liquidity sweep, NP-S1; ARCH-NP-005).
    assert len(recorded) == 5, "expected h001/h002/h003/h004/h007 anchored trades datasets"

    store = RecordStore(rebuild_bulk.JOURNAL)
    n_before = len(store)

    refs = rebuild_bulk.rebuild_all(verbose=False)
    assert set(refs) == set(recorded), "rebuild must cover exactly the anchored datasets"

    bulk = BulkStore(store, rebuild_bulk.BULK_ROOT)
    for ref, want in recorded.items():
        got = _sha256_file(bulk.path_for(ref))
        assert got == want, f"{ref}: rebuilt sha {got} != recorded {want}"
        bulk.read(ref)  # the store's own hash gate must also pass

    # A rebuild is a read, never a write: no records may be appended.
    assert len(RecordStore(rebuild_bulk.JOURNAL)) == n_before


def test_rebuild_all_reproduces_h007_manifest_byte_identically(rebuild_bulk):
    """ARCH-NP-005 regression: rebuild_all() dispatches the h007 lineage (previously
    a loud ``SystemExit`` on every invocation, NOTE-NP-003) and its rebuilt
    verdict_trades.h007_np_liquidity_sweep_v1_1 parquet matches the manifest's
    recorded sha256 exactly.

    Named and isolated deliberately, on top of the generic per-ref loop in
    ``test_rebuild_all_matches_recorded_manifests`` above: the byte-identity check
    itself is reused (the SAME ``rebuild_all()`` call and the SAME imported
    ``_sha256_file``/``BulkStore.path_for``, not a re-implementation of the
    hash comparison — see ``tests/scripts/test_ac1_engine_parity_np004.py``'s AC-1
    tests for the pipeline-level equivalent of this same comparison), so a future
    regression narrowed to just the h007 dispatch entry fails with an
    unmistakable, h007-named assertion rather than only the generic count/set
    check above.
    """
    store = RecordStore(rebuild_bulk.JOURNAL)
    hyps = {h.record_id: h for h in store.query(record_type="hypothesis")}
    h007_manifest_ref = None
    recorded_sha = None
    for v in store.query(record_type="verdict"):
        ref = v.payload.get("trades_manifest")
        if not ref:
            continue
        if hyps[v.payload["hypothesis_ref"]].payload["lineage"] == "h007_np_liquidity_sweep_v1_1":
            h007_manifest_ref = ref
            recorded_sha = store.get(ref).payload["file_sha256"]
    assert h007_manifest_ref is not None, "expected a judged h007 verdict in the journal"

    n_before = len(store)
    refs = rebuild_bulk.rebuild_all(verbose=False)  # raises SystemExit on ANY mismatch
    assert h007_manifest_ref in refs, "rebuild_all() did not dispatch the h007 lineage"

    bulk = BulkStore(store, rebuild_bulk.BULK_ROOT)
    got = _sha256_file(bulk.path_for(h007_manifest_ref))
    assert got == recorded_sha, f"h007 rebuild sha {got} != recorded {recorded_sha}"
    bulk.read(h007_manifest_ref)  # the store's own hash gate must also pass

    assert len(RecordStore(rebuild_bulk.JOURNAL)) == n_before, "rebuild must not append records"


def test_rebuild_refuses_unknown_lineage(rebuild_bulk):
    """A verdict lineage with no registered event builder is a loud failure."""
    import pandas as pd

    with pytest.raises(SystemExit, match="no event builder registered"):
        rebuild_bulk._events_for_lineage("h999_unregistered", None, pd.DataFrame())


# The driver runs in a FRESH interpreter (a genuine process restart) and prints
# {manifest_ref: sha} of every file it rebuilds.
_DRIVER = """
import json, importlib.util
from pathlib import Path
root = Path.cwd()
spec = importlib.util.spec_from_file_location("rebuild_bulk", root / "scripts" / "rebuild_bulk.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
refs = mod.rebuild_all(verbose=False)
from qrf.kernel.records.bulk import BulkStore, _sha256_file
from qrf.kernel.records.store import RecordStore
store = RecordStore(mod.JOURNAL); bulk = BulkStore(store, mod.BULK_ROOT)
print("SHAS=" + json.dumps({r: _sha256_file(bulk.path_for(r)) for r in refs}))
"""


def _rebuild_in_subprocess() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    proc = subprocess.run(
        [sys.executable, "-c", _DRIVER],
        cwd=str(ROOT), env=env, capture_output=True, text=True,
    )
    assert proc.returncode == 0, f"subprocess rebuild failed:\n{proc.stderr}"
    line = next(ln for ln in proc.stdout.splitlines() if ln.startswith("SHAS="))
    return json.loads(line[len("SHAS="):])


def test_rebuild_byte_stable_across_process_restart(rebuild_bulk):
    """Two independent fresh-interpreter rebuilds produce identical bytes, and
    both match the manifest bytes written by the original (separate) judge run."""
    recorded = _recorded_shas(rebuild_bulk)
    first = _rebuild_in_subprocess()
    second = _rebuild_in_subprocess()
    assert first == second, "rebuild is not deterministic across process restarts"
    assert first == recorded, "cross-process rebuild diverged from the recorded manifests"
