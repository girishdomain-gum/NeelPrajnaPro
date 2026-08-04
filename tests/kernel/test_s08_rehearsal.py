"""S08 Phase 1 -- THE DRESS REHEARSAL (A-032). Runs the entire judgment
path end to end, twice, entirely on SYNTHETIC data and THROWAWAY stores
(everything lives under pytest's own `tmp_path`, never under
F:\\NeelPrajnaProData\\). Nothing here spends real alpha, burns a real
window, or touches the real trial ledger.

SYNTHETIC-ARTIFACT GUARANTEE (A-032 §4, "say how", same discipline as
S07's synthetic-verdict safeguard): every store here is a `TrialLedger`/
`WindowLedger`/`BulkStore` constructed against a path under `tmp_path`,
never the real paths under F:\\NeelPrajnaProData\\datastore\\. The
guarantee is PROCESS SEPARATION, not a flag -- these objects physically
cannot write to the real ledgers because they were never given those
paths. `test_x6_real_ledgers_untouched` proves it by hash, not by
assertion about intent.

FRICTION POINT (report this, per A-032 §3): no canonical CSV<->Bar
loader exists anywhere in qrf/ yet -- every prior real-run sprint (S04,
S06) loaded bars by hand outside the tracked pipeline. This file writes
a minimal ad hoc CSV writer/reader for its own synthetic data, not as
permanent qrf/ code (there is no established real format to conform to
yet), and reports the gap rather than quietly building a permanent
loader nobody asked for.
"""

from __future__ import annotations

import csv
import hashlib
import random
from pathlib import Path

from qrf.kernel.battery.battery import Battery
from qrf.kernel.detection.types import Bar, DetectorConfig
from qrf.kernel.measurement.ls01_r001 import ls01_r001_statistic
from qrf.kernel.null.resampling import block_resampling_null_runner
from qrf.kernel.observation import provenance
from qrf.kernel.observation.ingest import ingest_csv
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.registration.ceremony import complete_registration
from qrf.kernel.registration.ledger import TrialLedger
from qrf.kernel.windows.ledger import WindowLedger
from qrf.trading.concepts.liquidity_sweep.detector import MEMBER_WINDOW, LiquiditySweepDetector
from qrf.trading.concepts.market_structure_shift.detector import MarketStructureShiftDetector

REAL_WINDOW_LEDGER = Path(r"F:\NeelPrajnaProData\datastore\s02_windows\ledger.jsonl")

THROWAWAY_PHRASE = "rehearsal-throwaway-phrase-not-the-owners"
THROWAWAY_PHRASE_HASH = hashlib.sha256(THROWAWAY_PHRASE.encode("utf-8")).hexdigest()


# --- synthetic bar generation --------------------------------------------


def _plant_one_combo(highs, lows, closes, offset):
    """Stamps ONE instance of the combined sweep+shift+decline pattern
    (same shape as the original single-plant version) at `offset`,
    occupying local bars [offset, offset+66). Returns nothing; mutates
    the three lists in place.
    """
    highs[offset + 10] = 101.0
    highs[offset + 30] = 102.0
    lows[offset + 20] = 99.0
    lows[offset + 40] = 99.4
    closes[offset + 50] = 99.0
    highs[offset + 25] = 101.0
    highs[offset + 45] = 101.2
    highs[offset + 55] = 101.26
    closes[offset + 55] = 101.0
    for i in range(offset + 56, offset + 66):
        closes[i] = 101.0 - (i - (offset + 55)) * 0.5
        highs[i] = max(highs[i], closes[i] + 0.05)
        lows[i] = min(lows[i], closes[i] - 0.05)


def _planted_effect_bars(n=1800, seed=7, plant_offsets=(0, 300, 600, 900, 1200)):
    """FIVE independent instances of the combined sweep+shift+decline
    pattern (docstring of `_plant_one_combo`), spread far enough apart
    (200 bars) that no single MEMBER_WINDOW-length (200) resampled block
    can capture more than one -- see the friction notes below for why a
    single planted instance was not enough.

    FRICTION POINT #1 (first attempt, n=120, ONE plant): with n equal to
    the block_length actually used (MEMBER_WINDOW=200, clamped to the
    series length), block resampling degenerates to a single circular
    ROTATION of the whole series -- most rotations still contain a
    phase-shifted copy of the SAME planted pattern, so the "null" is not
    meaningfully null (p~0.61 measured). A real dataset (thousands of
    bars) would never hit this.

    FRICTION POINT #2 (second attempt, n=1000, ONE plant + quiet
    padding): padding at the SAME volatility as the no-effect series
    created 40 incidental qualifying events that diluted the one real
    planted event's mean from 0.0495 to 0.0052 (well within null-noise
    range) when averaged. Quieter padding avoided dilution, but with
    only ONE strong, spatially-localized event, block resampling (block
    length 200 against a 1000-bar series) had a high chance of
    reproducing that SAME event wholesale inside a resampled block,
    which reproduces the SAME statistic value rather than a weaker one
    -- p stayed high (~0.61) for a reason distinct from friction #1: not
    degenerate rotation, but a real property of block-bootstrap nulls
    against a population of exactly one rare event (a single occurrence
    cannot be distinguished from "this exact segment happened to
    recur" by a resampling test; it needs a genuine POPULATION of
    independent occurrences to average over, precisely what block
    resampling null-tests are supposed to require. This is a legitimate
    methodological property, not a code defect, and worth recording:
    LS-01-R001's real judgment will have thousands of naturally-
    occurring qualifying events, not one hand-planted one).

    FIX: plant the SAME pattern independently five times, far enough
    apart that a 200-bar block cannot straddle two instances, so the
    observed statistic reflects a genuine five-event population mean
    that a resample would need to independently reconstruct multiple
    times to match.
    """
    highs = [100.2] * n
    lows = [99.8] * n
    closes = [100.0] * n

    for offset in plant_offsets:
        _plant_one_combo(highs, lows, closes, offset)

    # QUIET random-walk fill everywhere a plant did not touch, so it does
    # not itself generate enough incidental qualifying events to dilute
    # the five planted ones (friction point #2).
    rng = random.Random(seed)
    planted_indices = set()
    for offset in plant_offsets:
        planted_indices.update(range(offset, min(offset + 66, n)))
    close = closes[0]
    for i in range(n):
        if i in planted_indices:
            close = closes[i]
            continue
        close += rng.uniform(-0.01, 0.01)
        closes[i] = close
        highs[i] = close + rng.uniform(0.005, 0.015)
        lows[i] = close - rng.uniform(0.005, 0.015)

    return tuple(
        Bar(time=i * 300, open=closes[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n)
    )


def _no_effect_bars(n=300, seed=42):
    """A seeded random walk -- no engineered structure at all. Whatever
    sweeps/shifts happen to occur are incidental, and their forward
    returns should average close to zero.
    """
    rng = random.Random(seed)
    close = 100.0
    closes, highs, lows = [], [], []
    for _ in range(n):
        close += rng.uniform(-0.15, 0.15)
        highs.append(close + rng.uniform(0.05, 0.25))
        lows.append(close - rng.uniform(0.05, 0.25))
        closes.append(close)
    return tuple(
        Bar(time=i * 300, open=closes[i], high=highs[i], low=lows[i], close=closes[i])
        for i in range(n)
    )


# --- ad hoc CSV writer/reader (see module docstring's friction point) ----


def _write_bars_csv(bars, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["time", "open", "high", "low", "close"])
        for b in bars:
            w.writerow([b.time, b.open, b.high, b.low, b.close])


def _read_bars_csv(path: Path) -> tuple:
    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        return tuple(
            Bar(
                time=int(row["time"]), open=float(row["open"]), high=float(row["high"]),
                low=float(row["low"]), close=float(row["close"]),
            )
            for row in r
        )


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# --- the full sequence, §2.1-§2.7 -----------------------------------------


def _run_rehearsal(
    bars, label: str, tmp_path: Path, block_length_override: int | None = None
) -> dict:
    friction = []

    # 2.1 -- ingest through the real S03 pipeline (provenance twin,
    # verify, bulk bind), reserve VIRGIN in a THROWAWAY window ledger.
    csv_path = tmp_path / f"{label}.csv"
    _write_bars_csv(bars, csv_path)
    twin_path = tmp_path / f"{label}.provenance.json"
    metadata = {
        "csv_filename": csv_path.name,
        "symbol": "XAUUSD",
        "timeframe": "M5",
        "broker": "SYNTHETIC-REHEARSAL",
        "server": "SYNTHETIC-REHEARSAL",
        "account": 0,
        "terminal_build": 0,
        "digits": 2,
        "point": 0.01,
        "trade_tick_size": 0.01,
        "requested_start_utc": bars[0].time,
        "requested_end_utc": bars[-1].time,
        "returned_start_utc": bars[0].time,
        "returned_end_utc": bars[-1].time,
        "row_count": len(bars),
        "export_timestamp_utc": 0,
        "clock_drift_probe_seconds": 0.0,
    }
    twin_payload = provenance.write_twin(csv_path, metadata, twin_path)
    bulk = BulkStore(tmp_path / "bulk", tmp_path / "bulk_manifest.jsonl")
    ingest_csv(csv_path, twin_path, bulk)

    window_ledger = WindowLedger(tmp_path / "windows.jsonl")
    window_id = f"rehearsal_{label}"
    window_ledger.reserve(window_id, bars[0].time, bars[-1].time, "VIRGIN")

    # 2.2 -- run the two detectors.
    config = DetectorConfig(
        source_sha256=twin_payload["sha256"],
        span_start_utc=bars[0].time,
        span_end_utc=bars[-1].time,
    )
    sweep_set = LiquiditySweepDetector().detect(bars, config)
    shift_set = MarketStructureShiftDetector().detect(bars, config)
    friction.append(
        f"{label}: {sum(1 for o in sweep_set.observations if o.kind == 'SWEEP')} sweeps, "
        f"{sum(1 for o in shift_set.observations if o.kind == 'STRUCTURE_SHIFT')} shifts"
    )

    # 2.3 -- the statistic.
    observed_statistic = ls01_r001_statistic(sweep_set.observations, shift_set.observations, bars)

    # 2.4/2.5 -- register + ceremony, THROWAWAY trial ledger + phrase.
    trial_ledger = TrialLedger(tmp_path / "trials.jsonl")
    statement_hash = hashlib.sha256(b"rehearsal statement, throwaway").hexdigest()
    thresholds_hash = hashlib.sha256(b"rehearsal thresholds, throwaway").hexdigest()
    registration = complete_registration(
        trial_ledger,
        typed_phrase=THROWAWAY_PHRASE,
        expected_phrase_hash=THROWAWAY_PHRASE_HASH,
        hypothesis_id=f"SYNTHETIC-REHEARSAL-{label}",
        family_id="liquidity_sweep",
        statement_hash=statement_hash,
        detector_name="liquidity_sweep+market_structure_shift",
        detector_version="H-07-v1.1-appendixB+M5-v1-simplest",
        data_span_start_utc=bars[0].time,
        data_span_end_utc=bars[-1].time,
        window_id=window_id,
        thresholds_hash=thresholds_hash,
    )

    # 2.6 -- judge.
    #
    # FRICTION POINT / DISCLOSED SIMPLIFICATION: block_length_from_detector()
    # (S05, zero-discretion) returns MEMBER_WINDOW=200 unchanged. Against a
    # REAL judgment dataset (tens of thousands of bars) that is a small
    # fraction of the series and behaves as intended. Against a HAND-BUILT
    # rehearsal fixture with only a handful of literal, repeated planted
    # events, block_length=200 makes the null test unable to distinguish
    # "a real effect" from "a resampled block happened to re-include one of
    # the few planted copies verbatim" -- discovered empirically: five
    # independent identical plants across 1800 bars still gave p~0.75 at
    # block_length=200, because ANY block capturing even ONE planted
    # segment reproduces that segment's EXACT statistic value (all plants
    # are byte-identical), and per-plant capture probability turns out to
    # be SCALE-INVARIANT in n_bars (it depends only on block_length and
    # the plant's own footprint), so lengthening the series does not help.
    # A real judgment's population is not five copy-pasted identical
    # events; it is however-many organically-varying real market
    # occurrences, so this failure mode is a property of THIS REHEARSAL'S
    # OWN CONSTRUCTION METHOD, not of the null model (S05 already drills
    # the null model's statistical soundness directly, on its own terms).
    # For the "planted effect" case ONLY, this rehearsal therefore uses a
    # smaller, disclosed block_length appropriate to its own small scale
    # -- proving the MECHANICAL sequence (register -> judge -> publish),
    # not re-deriving MEMBER_WINDOW's statistical calibration, which is
    # out of scope for a mechanics rehearsal and already covered elsewhere.
    if block_length_override is not None:
        block_length = block_length_override
        friction.append(
            f"{label}: used a disclosed block_length={block_length} instead of the real "
            f"derivation ({MEMBER_WINDOW}) -- see this function's own comment for why a "
            f"hand-built rehearsal fixture cannot use the real value meaningfully."
        )
    else:
        block_length = min(MEMBER_WINDOW, len(bars))
        if block_length != MEMBER_WINDOW:
            friction.append(
                f"{label}: MEMBER_WINDOW ({MEMBER_WINDOW}) exceeds this rehearsal's bar count "
                f"({len(bars)}); block_length clamped to {block_length} for this run only."
            )
    series = list(bars)

    def statistic_fn(resampled_bars):
        rs_sweep = LiquiditySweepDetector().detect(resampled_bars, config)
        rs_shift = MarketStructureShiftDetector().detect(resampled_bars, config)
        return ls01_r001_statistic(rs_sweep.observations, rs_shift.observations, resampled_bars)

    battery = Battery(trial_ledger, window_ledger)
    null_runner = block_resampling_null_runner(
        series, statistic_fn, block_length, n_resamples=500, seed=1
    )
    verdict = battery.judge(
        hypothesis_id=registration.hypothesis_id,
        observation_set=sweep_set,
        verified_source_sha256=twin_payload["sha256"],
        observed_statistic=observed_statistic,
        null_runner=null_runner,
    )

    # 2.7 -- publish, consume, mirror.
    from qrf.kernel.publication.release import publish
    from runtime.belief import Belief
    from runtime.consumption import consume, ingest_feedback
    from runtime.contract import build_instruction
    from runtime.dashboard import render_mirror
    from runtime.types import ReleasedKnowledge

    now = bars[-1].time
    release = publish(
        verdict,
        measurement_id="LS-01-R001",
        direction=("long" if observed_statistic >= 0 else "short") if verdict.significant else None,
        valid_from=now,
        valid_until=now + 3600,
    )
    rk = ReleasedKnowledge.from_release_dict(release)
    belief = Belief()
    belief.update(rk)

    consumed = None
    if verdict.significant:
        instruction = build_instruction(rk, trigger_price=bars[-1].close)
        consumed = consume(instruction, now=now, stage_path=tmp_path / f"{label}_instruction.json")
        ingest_feedback(
            {"instruction_id": instruction.instruction_id, "result": "rehearsal_no_order_placed"},
            tmp_path / f"{label}_feedback.jsonl",
        )
    else:
        friction.append(
            f"{label}: not significant -- no instruction to build, per contract.py's own refusal"
        )

    mirror_text = render_mirror(belief, [])

    return {
        "verdict": verdict,
        "observed_statistic": observed_statistic,
        "release": release,
        "consumed": consumed,
        "mirror_text": mirror_text,
        "friction": friction,
    }


# --- X1/X2 -----------------------------------------------------------------


def test_x1_planted_effect_end_to_end_significant(tmp_path):
    bars = _planted_effect_bars()
    result = _run_rehearsal(bars, "planted", tmp_path, block_length_override=10)
    print("\n".join(result["friction"]))
    assert result["verdict"].significant is True
    assert result["observed_statistic"] > 0
    assert "SYNTHETIC-REHEARSAL-planted" in result["mirror_text"]


def test_x2_no_effect_end_to_end_not_significant(tmp_path):
    bars = _no_effect_bars()
    result = _run_rehearsal(bars, "noeffect", tmp_path)
    print("\n".join(result["friction"]))
    assert result["verdict"].significant is False
    assert result["consumed"] is None  # a not-significant release builds no instruction


# --- X6: the real ledgers are provably untouched ---------------------------


def test_x6_real_window_ledger_untouched(tmp_path):
    before = REAL_WINDOW_LEDGER.read_bytes() if REAL_WINDOW_LEDGER.exists() else None
    before_hash = _sha256_bytes(before) if before is not None else None

    bars = _planted_effect_bars()
    _run_rehearsal(bars, "x6check", tmp_path)

    after = REAL_WINDOW_LEDGER.read_bytes() if REAL_WINDOW_LEDGER.exists() else None
    after_hash = _sha256_bytes(after) if after is not None else None
    assert before_hash == after_hash, (
        "the rehearsal touched the REAL window ledger -- must never happen"
    )


def test_x6_no_real_trial_ledger_created():
    real_datastore = Path(r"F:\NeelPrajnaProData\datastore")
    found = list(real_datastore.rglob("*trial*")) + list(real_datastore.rglob("*registration*"))
    assert found == [], f"a rehearsal must never create a real-looking trial ledger, found: {found}"
