"""MT5 bar-CSV adapter — the data-plane door for the trading plug-in.

Implementation Blueprint v1.0 §5 arrows (1)-(4), §7 Sprint 3; REV-S2 OBS-4.

Contract
--------
(a) **OBS-4 (normative).** An MT5 bar's ``time`` is its OPEN time. This adapter
    emits ``ts`` = CLOSE time = ``open + timeframe_seconds`` as int64 nanoseconds
    on the UTC timeline. ``timeframe_seconds`` is an explicit **required**
    parameter — the timeframe is never inferred from the data. Sprint-2
    detectors trust that ``ts`` holds close times (RSIDetector, SeasonalityDetector),
    so this normalization is load-bearing.

(b) **Validate at the door; flag, never repair, never drop.** The pandera schema
    (``adapters/schemas.py``) rejects only structural faults. Every value-level
    anomaly is *flagged* and the row is quarantined unchanged:

      - ``non_monotonic``   time not strictly increasing vs the previous row
      - ``duplicate``       time equal to the previous row's time
      - ``gap``             a hole wider than ``gap_k x timeframe`` not explained
                            by a weekend or a declared holiday
      - ``high_lt_low``     high < low
      - ``nonpositive_price`` any of O/H/L/C <= 0
      - ``spread_outlier``  spread present and a robust (MAD) outlier

    Flagged rows go to the ``{dataset}__flagged`` quarantine dataset; clean rows
    to ``{dataset}`` — both via :class:`BulkStore` with manifests. Nothing is
    ever modified or discarded (arrow (2): "never repairs — flags").

(c) **ingest_report.** One record per ingest, parented to the manifests, verdict
    PASS unless the flagged share exceeds ``flagged_threshold`` (then FAIL — the
    data is still stored in full; a FAIL verdict deletes nothing).

The weekend/holiday gap allowance is a *documented, parameterized* rule pending
Architect ratification (DEVQ-006); the quarantine naming convention pends
DEVQ-007.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pyarrow as pa

from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.record import Record
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters.schemas import OPTIONAL_COLUMNS, to_canonical

NS_PER_SEC = 1_000_000_000
_SECS_PER_DAY = 86_400
# 1970-01-01 was a Thursday; (epoch_day + 3) % 7 gives Mon=0 .. Sun=6.
_EPOCH_WEEKDAY_OFFSET = 3

# Anomaly class labels (stable identifiers used in flags and anomaly_counts).
NON_MONOTONIC = "non_monotonic"
DUPLICATE = "duplicate"
GAP = "gap"
HIGH_LT_LOW = "high_lt_low"
NONPOSITIVE_PRICE = "nonpositive_price"
SPREAD_OUTLIER = "spread_outlier"
ANOMALY_CLASSES: tuple[str, ...] = (
    NON_MONOTONIC,
    DUPLICATE,
    GAP,
    HIGH_LT_LOW,
    NONPOSITIVE_PRICE,
    SPREAD_OUTLIER,
)

# Columns persisted to the store (canonical bar + close-time ts).
_BASE_STORE_COLUMNS = ("ts", "time", "open", "high", "low", "close")

# Reserved quarantine-dataset suffix (DEVQ-007 ruling): flagged rows for
# ``{dataset}`` live in ``{dataset}__flagged``. A caller dataset name may not
# itself contain this suffix — the adapter rejects it at the door.
QUARANTINE_SUFFIX = "__flagged"


def compute_close_ts(open_sec: int, timeframe_seconds: int) -> int:
    """OBS-4: close-time ``ts`` in int64 ns from an OPEN time in seconds."""
    return int(open_sec + timeframe_seconds) * NS_PER_SEC


def _weekday(sec: int) -> int:
    """UTC weekday, Mon=0 .. Sun=6, by epoch arithmetic (matches the detectors)."""
    return ((sec // _SECS_PER_DAY) + _EPOCH_WEEKDAY_OFFSET) % 7


def _utc_date(sec: int) -> str:
    return datetime.fromtimestamp(sec, UTC).strftime("%Y-%m-%d")


def build_bar_frame(canonical: pd.DataFrame, timeframe_seconds: int) -> pd.DataFrame:
    """Add the OBS-4 close-time ``ts`` (int64 ns) to a canonical bar frame.

    ``time`` (open seconds) is preserved so lineage back to the source bar and
    the OBS-4 property (``ts == (time + timeframe) * 1e9``) stay checkable.
    """
    if timeframe_seconds <= 0:
        from qrf.kernel.errors import SchemaViolation

        raise SchemaViolation("timeframe_seconds must be a positive integer")
    df = canonical.reset_index(drop=True).copy()
    df["time"] = df["time"].astype("int64")
    df["ts"] = (df["time"] + int(timeframe_seconds)) * NS_PER_SEC
    df["ts"] = df["ts"].astype("int64")
    return df


def _gap_excused(
    t0: int, t1: int, timeframe_seconds: int, weekend_allowance: bool, holidays: frozenset[str]
) -> bool:
    """Is the hole between open times ``t0`` and ``t1`` weekend/holiday-explained?

    Any expected-but-missing bar open time (``t0+tf, t0+2tf, ... t1-tf``) that
    falls on a weekend day, or on a declared holiday UTC date, excuses the whole
    hole. Documented simplification pending DEVQ-006.
    """
    step = int(timeframe_seconds)
    for cand in range(int(t0) + step, int(t1), step):
        if weekend_allowance and _weekday(cand) in (5, 6):
            return True
        if holidays and _utc_date(cand) in holidays:
            return True
    return False


def flag_anomalies(
    frame: pd.DataFrame,
    *,
    timeframe_seconds: int,
    gap_k: float = 1.0,
    weekend_allowance: bool = True,
    holidays: frozenset[str] | set[str] | None = None,
    spread_mad_k: float = 5.0,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Attach a ``flags`` list to each row and return ``(frame, anomaly_counts)``.

    ``frame`` must already carry ``time`` (open seconds) and ``ts``. Rows are
    examined in input order. A ``gap`` fires when the hole beyond one bar-width
    exceeds ``gap_k x timeframe`` and is not weekend/holiday-explained. No row is
    modified or dropped; ``anomaly_counts[class]`` counts rows exhibiting it.
    """
    holidays_fs = frozenset(holidays or ())
    df = frame.reset_index(drop=True)
    n = len(df)
    flags: list[list[str]] = [[] for _ in range(n)]

    time = df["time"].astype("int64").tolist()
    o = df["open"].astype("float64").tolist()
    h = df["high"].astype("float64").tolist()
    low = df["low"].astype("float64").tolist()
    c = df["close"].astype("float64").tolist()

    tf = int(timeframe_seconds)
    for i in range(n):
        if i > 0:
            delta = time[i] - time[i - 1]
            if delta == 0:
                flags[i].append(DUPLICATE)
            elif delta < 0:
                flags[i].append(NON_MONOTONIC)
            else:
                hole = delta - tf
                if hole > gap_k * tf and not _gap_excused(
                    time[i - 1], time[i], tf, weekend_allowance, holidays_fs
                ):
                    flags[i].append(GAP)
        if h[i] < low[i]:
            flags[i].append(HIGH_LT_LOW)
        if min(o[i], h[i], low[i], c[i]) <= 0:
            flags[i].append(NONPOSITIVE_PRICE)

    # Spread outliers (robust), only when a spread column is present + numeric.
    # Scale is the median absolute deviation; when MAD collapses to 0 (most
    # spreads identical) fall back to the mean absolute deviation so a lone
    # extreme value is still caught. All-identical spreads -> no outliers.
    if "spread" in df.columns:
        s = pd.to_numeric(df["spread"], errors="coerce")
        present = s.dropna()
        if len(present) >= 3:
            median = float(present.median())
            deviations = (present - median).abs()
            scale = float(deviations.median()) or float(deviations.mean())
            if scale > 0:
                for i in range(n):
                    v = s.iloc[i]
                    if pd.notna(v) and abs(float(v) - median) > spread_mad_k * scale:
                        flags[i].append(SPREAD_OUTLIER)

    out = df.copy()
    out["flags"] = flags
    counts: dict[str, int] = {}
    for cls in ANOMALY_CLASSES:
        cnt = sum(1 for fl in flags if cls in fl)
        if cnt:
            counts[cls] = cnt
    return out, counts


@dataclass(frozen=True)
class IngestResult:
    """Outcome of :func:`ingest_mt5_csv` — the report plus what the caller needs."""

    report: Record
    manifest_refs: list[str]
    clean_manifest: str | None
    flagged_manifest: str | None
    rows_total: int
    rows_clean: int
    rows_flagged: int
    ts_min: int
    ts_max: int
    anomaly_counts: dict[str, int]
    verdict: str


def _to_store_table(df: pd.DataFrame, *, with_flags: bool) -> pa.Table:
    """Build the pyarrow table persisted for one partition (clean or flagged)."""
    cols: dict[str, pa.Array] = {
        "ts": pa.array(df["ts"].astype("int64"), type=pa.int64()),
        "time": pa.array(df["time"].astype("int64"), type=pa.int64()),
        "open": pa.array(df["open"].astype("float64"), type=pa.float64()),
        "high": pa.array(df["high"].astype("float64"), type=pa.float64()),
        "low": pa.array(df["low"].astype("float64"), type=pa.float64()),
        "close": pa.array(df["close"].astype("float64"), type=pa.float64()),
    }
    for vc in OPTIONAL_COLUMNS:
        if vc in df.columns:
            numeric = pd.to_numeric(df[vc], errors="coerce").astype("float64")
            cols[vc] = pa.array(numeric, type=pa.float64())
    if with_flags:
        cols["flags"] = pa.array([",".join(fl) for fl in df["flags"]], type=pa.string())
    names = [c for c in _BASE_STORE_COLUMNS if c in cols]
    names += [vc for vc in OPTIONAL_COLUMNS if vc in cols]
    if with_flags:
        names.append("flags")
    return pa.Table.from_arrays([cols[n] for n in names], names=names)


def ingest_mt5_csv(
    csv_path: str | Path,
    dataset: str,
    *,
    timeframe_seconds: int,
    store: RecordStore,
    bulk_store: BulkStore,
    column_map: dict[str, str] | None = None,
    gap_k: float = 1.0,
    weekend_allowance: bool = True,
    holidays: frozenset[str] | set[str] | None = None,
    spread_mad_k: float = 5.0,
    flagged_threshold: float = 0.05,
    producer: str = "adapter:mt5_csv",
) -> IngestResult:
    """Ingest an MT5 bar CSV: validate, flag, quarantine, and report.

    Clean rows -> ``{dataset}``; flagged rows -> ``{dataset}__flagged``; both via
    :class:`BulkStore` manifests. Emits an ``ingest_report`` (schema v2: records
    the ``params`` used, DEVQ-006; parents = the manifests). Verdict FAIL iff
    ``rows_flagged / rows_total > flagged_threshold`` — data stored in full either
    way. The dataset name may not contain the reserved ``__flagged`` suffix
    (DEVQ-007) — rejected at the door.
    """
    if QUARANTINE_SUFFIX in dataset:
        from qrf.kernel.errors import SchemaViolation

        raise SchemaViolation(
            f"dataset name {dataset!r} contains the reserved quarantine suffix "
            f"{QUARANTINE_SUFFIX!r} (DEVQ-007); choose a name without it"
        )
    raw = pd.read_csv(csv_path)
    canonical = to_canonical(raw, column_map)
    frame = build_bar_frame(canonical, timeframe_seconds)
    flagged_frame, anomaly_counts = flag_anomalies(
        frame,
        timeframe_seconds=timeframe_seconds,
        gap_k=gap_k,
        weekend_allowance=weekend_allowance,
        holidays=holidays,
        spread_mad_k=spread_mad_k,
    )

    is_clean = flagged_frame["flags"].map(len) == 0
    clean_df = flagged_frame[is_clean]
    quarantine_df = flagged_frame[~is_clean]
    rows_total = len(flagged_frame)
    rows_clean = int(len(clean_df))
    rows_flagged = int(len(quarantine_df))

    manifest_refs: list[str] = []
    clean_manifest: str | None = None
    flagged_manifest: str | None = None

    if rows_clean:
        rec = bulk_store.write(
            dataset, _to_store_table(clean_df, with_flags=False),
            producer=producer, parents=[],
        )
        clean_manifest = rec.record_id
        manifest_refs.append(rec.record_id)
    if rows_flagged:
        rec = bulk_store.write(
            f"{dataset}{QUARANTINE_SUFFIX}", _to_store_table(quarantine_df, with_flags=True),
            producer=producer, parents=[],
        )
        flagged_manifest = rec.record_id
        manifest_refs.append(rec.record_id)

    ts_all = frame["ts"].astype("int64")
    ts_min = int(ts_all.min())
    ts_max = int(ts_all.max())

    flagged_share = (rows_flagged / rows_total) if rows_total else 0.0
    verdict = "FAIL" if flagged_share > flagged_threshold else "PASS"

    # ingest_report v2 (DEVQ-006): the parameters ride with the report so a
    # holiday-excused gap (or any verdict) is reconstructable from the ledger.
    params = {
        "timeframe_seconds": int(timeframe_seconds),
        "gap_k": float(gap_k),
        "weekend_allowance": bool(weekend_allowance),
        "holidays": sorted(holidays or ()),
        "spread_mad_k": float(spread_mad_k),
        "flagged_threshold": float(flagged_threshold),
        "dataset": dataset,
    }
    report = store.append(
        "ingest_report",
        {
            "manifest_refs": manifest_refs,
            "rows_clean": rows_clean,
            "rows_flagged": rows_flagged,
            "anomaly_counts": anomaly_counts,
            "verdict": verdict,
            "params": params,
        },
        producer=producer,
        event_ts=ts_max,
        parents=manifest_refs,
        schema_version=2,
    )
    return IngestResult(
        report=report,
        manifest_refs=manifest_refs,
        clean_manifest=clean_manifest,
        flagged_manifest=flagged_manifest,
        rows_total=rows_total,
        rows_clean=rows_clean,
        rows_flagged=rows_flagged,
        ts_min=ts_min,
        ts_max=ts_max,
        anomaly_counts=anomaly_counts,
        verdict=verdict,
    )
