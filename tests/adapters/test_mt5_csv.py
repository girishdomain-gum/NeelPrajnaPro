"""MT5 CSV adapter tests (Blueprint §5, ARCH-003).

OBS-4 close-time property; each anomaly class planted and flagged; quarantine
integrity (rows stored unmodified); clean+flagged == input; ingest_report
independent count; threshold FAIL path; column-mapping variants; door rejection;
and the real Sprint-2 export ingesting with zero flags.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow as pa
import pytest

from qrf.kernel.errors import SchemaViolation
from qrf.kernel.records.bulk import BulkStore
from qrf.kernel.records.store import RecordStore
from qrf.trading.adapters import mt5_csv as A
from qrf.trading.adapters.schemas import IVF_S2_COLUMN_MAP

TF = 3600
REPO_ROOT = Path(__file__).resolve().parents[2]

# A Wednesday midday anchor (2024-01-03 12:00 UTC) — weekday, no weekend/holiday.
WED_NOON = 1_704_283_200
# Friday 23:00 / Monday 01:00 across the 2024-01-06/07 weekend.
FRI_2300 = 1_704_495_600  # 2024-01-05 23:00 UTC
MON_0100 = 1_704_675_600  # 2024-01-08 01:00 UTC


@pytest.fixture
def env(tmp_path):
    store = RecordStore(tmp_path / "journal.jsonl")
    return store, BulkStore(store, tmp_path / "bulk")


def _canon(times, *, o=None, h=None, low=None, c=None, spread=None):
    n = len(times)
    o = o if o is not None else [100.0] * n
    h = h if h is not None else [101.0] * n
    low = low if low is not None else [99.0] * n
    c = c if c is not None else [100.5] * n
    data = {"time": times, "open": o, "high": h, "low": low, "close": c}
    if spread is not None:
        data["spread"] = spread
    return pd.DataFrame(data)


def _flags(df, **kw):
    frame = A.build_bar_frame(df, TF)
    flagged, counts = A.flag_anomalies(frame, timeframe_seconds=TF, **kw)
    return [list(x) for x in flagged["flags"]], counts


def _write_csv(tmp_path, df, name="bars.csv"):
    p = tmp_path / name
    df.to_csv(p, index=False)
    return p


# --- OBS-4 -------------------------------------------------------------------
def test_obs4_close_ts_property():
    times = [WED_NOON + i * TF for i in range(10)]
    frame = A.build_bar_frame(_canon(times), TF)
    for i in range(len(times)):
        assert int(frame["ts"].iloc[i]) == A.compute_close_ts(times[i], TF)
        assert int(frame["ts"].iloc[i]) == (times[i] + TF) * A.NS_PER_SEC


# --- each anomaly class planted and flagged ----------------------------------
def test_flag_non_monotonic():
    flags, counts = _flags(_canon([WED_NOON, WED_NOON - TF]))
    assert A.NON_MONOTONIC in flags[1]
    assert counts == {A.NON_MONOTONIC: 1}


def test_flag_duplicate():
    flags, counts = _flags(_canon([WED_NOON, WED_NOON]))
    assert A.DUPLICATE in flags[1]
    assert counts.get(A.DUPLICATE) == 1


def test_flag_gap_unexcused_weekday():
    flags, counts = _flags(_canon([WED_NOON, WED_NOON + 4 * TF]))  # 3-bar hole, midweek
    assert A.GAP in flags[1]
    assert counts.get(A.GAP) == 1


def test_gap_excused_by_weekend():
    flags, counts = _flags(_canon([FRI_2300, MON_0100]))
    assert flags[1] == []  # weekend spans the hole -> no gap flag
    assert A.GAP not in counts


def test_gap_excused_by_holiday_parameter():
    times = [WED_NOON, WED_NOON + 4 * TF]
    assert A.GAP in _flags(_canon(times))[0][1]  # flags without the allowance
    flags, _ = _flags(_canon(times), holidays={"2024-01-03"})
    assert flags[1] == []  # declared holiday excuses the same hole


def test_flag_high_lt_low():
    flags, counts = _flags(_canon([WED_NOON, WED_NOON + TF], h=[101.0, 90.0], low=[99.0, 95.0]))
    assert A.HIGH_LT_LOW in flags[1]
    assert counts.get(A.HIGH_LT_LOW) == 1


def test_flag_nonpositive_price():
    flags, counts = _flags(_canon([WED_NOON, WED_NOON + TF], c=[100.5, 0.0]))
    assert A.NONPOSITIVE_PRICE in flags[1]
    assert counts.get(A.NONPOSITIVE_PRICE) == 1


def test_flag_spread_outlier():
    times = [WED_NOON + i * TF for i in range(11)]
    spread = [10.0] * 10 + [10_000.0]
    flags, counts = _flags(_canon(times, spread=spread))
    assert A.SPREAD_OUTLIER in flags[10]
    assert counts.get(A.SPREAD_OUTLIER) == 1
    # A normal-spread feed flags nothing.
    flags2, _ = _flags(_canon(times, spread=[10.0] * 11))
    assert all(f == [] for f in flags2)


# --- full ingest: counts, quarantine integrity, report -----------------------
def test_ingest_counts_quarantine_and_report(env, tmp_path):
    store, bulk = env
    # 5 hourly bars: row 2 duplicates row 1; row 4 has high<low. -> 2 flagged.
    times = [WED_NOON, WED_NOON + TF, WED_NOON + TF, WED_NOON + 2 * TF, WED_NOON + 3 * TF]
    df = _canon(times, h=[101, 101, 101, 101, 90], low=[99, 99, 99, 99, 95])
    csv = _write_csv(tmp_path, df)

    res = A.ingest_mt5_csv(csv, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk)

    assert res.rows_total == 5
    assert res.rows_clean + res.rows_flagged == 5
    assert res.rows_flagged == 2
    # ingest_report independently agrees.
    rep = res.report.payload
    assert rep["rows_clean"] == res.rows_clean and rep["rows_flagged"] == 2
    assert rep["anomaly_counts"].get(A.DUPLICATE) == 1
    assert rep["anomaly_counts"].get(A.HIGH_LT_LOW) == 1
    assert set(rep["manifest_refs"]) == set(res.manifest_refs)
    assert res.report.record_type == "ingest_report"
    assert res.report.parents == tuple(res.manifest_refs)

    # Quarantine holds the flagged rows, unmodified, with a flags column.
    q = bulk.read(res.flagged_manifest)
    assert q.num_rows == 2
    assert "flags" in q.schema.names
    dup_row = q.to_pylist()[0]
    assert "duplicate" in dup_row["flags"] or "high_lt_low" in dup_row["flags"]
    # Clean partition holds exactly the unflagged rows.
    assert bulk.read(res.clean_manifest).num_rows == 3
    assert store.verify().ok


def test_threshold_fail_still_stores_everything(env, tmp_path):
    store, bulk = env
    # 4 bars, 2 flagged -> share 0.5 > threshold -> FAIL, but data is kept.
    times = [WED_NOON, WED_NOON, WED_NOON + TF, WED_NOON + 2 * TF]  # row1 dup
    df = _canon(times, c=[100.5, 100.5, -1.0, 100.5])  # row2 nonpositive
    csv = _write_csv(tmp_path, df)

    res = A.ingest_mt5_csv(
        csv, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk, flagged_threshold=0.05
    )
    assert res.verdict == "FAIL"
    assert res.report.payload["verdict"] == "FAIL"
    # Nothing deleted: both partitions present and readable.
    assert bulk.read(res.clean_manifest).num_rows == res.rows_clean
    assert bulk.read(res.flagged_manifest).num_rows == res.rows_flagged
    assert res.rows_clean + res.rows_flagged == 4


def test_column_mapping_variant(env, tmp_path):
    store, bulk = env
    df = pd.DataFrame(
        {"t": [WED_NOON, WED_NOON + TF], "o": [1, 2], "h": [2, 3], "l": [0.5, 1.5], "c": [1.5, 2.5]}
    )
    csv = _write_csv(tmp_path, df)
    cmap = {"time": "t", "open": "o", "high": "h", "low": "l", "close": "c"}
    res = A.ingest_mt5_csv(
        csv, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk, column_map=cmap
    )
    assert res.rows_total == 2 and res.rows_flagged == 0


def test_door_rejects_missing_required_column(env, tmp_path):
    store, bulk = env
    df = pd.DataFrame({"time": [WED_NOON], "open": [1], "high": [2], "low": [0.5]})  # no close
    csv = _write_csv(tmp_path, df)
    with pytest.raises(SchemaViolation):
        A.ingest_mt5_csv(csv, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk)


def test_door_rejects_reserved_flagged_suffix(env, tmp_path):
    """DEVQ-007: a dataset name containing __flagged is refused at the door."""
    store, bulk = env
    df = _canon([WED_NOON, WED_NOON + TF])
    csv = _write_csv(tmp_path, df)
    with pytest.raises(SchemaViolation) as ei:
        A.ingest_mt5_csv(csv, "ds__flagged", timeframe_seconds=TF, store=store, bulk_store=bulk)
    assert A.QUARANTINE_SUFFIX in str(ei.value)
    # Nothing was written (rejected before any manifest).
    assert list(store.query(record_type="bulk_manifest")) == []


def test_ingest_report_v2_records_params(env, tmp_path):
    """DEVQ-006: the ingest_report is schema v2 and records the params used."""
    store, bulk = env
    df = _canon([WED_NOON, WED_NOON + TF])
    csv = _write_csv(tmp_path, df)
    res = A.ingest_mt5_csv(
        csv, "ds", timeframe_seconds=TF, store=store, bulk_store=bulk,
        holidays={"2024-01-15", "2024-01-01"}, gap_k=1.0, flagged_threshold=0.05,
    )
    assert res.report.schema_version == 2
    params = res.report.payload["params"]
    assert params == {
        "timeframe_seconds": TF,
        "gap_k": 1.0,
        "weekend_allowance": True,
        "holidays": ["2024-01-01", "2024-01-15"],  # sorted
        "spread_mad_k": 5.0,
        "flagged_threshold": 0.05,
        "dataset": "ds",
    }
    assert store.verify().ok


# --- the real Sprint-2 export ingests clean (AC) -----------------------------
def test_real_ivf_export_ingests_zero_flags(env):
    store, bulk = env
    csv = REPO_ROOT / "IVF_S2_XAUUSD_PERIOD_H1.csv"
    res = A.ingest_mt5_csv(
        csv, "xauusd_h1_sample", timeframe_seconds=TF, store=store, bulk_store=bulk,
        column_map=IVF_S2_COLUMN_MAP, holidays={"2024-01-15"},
    )
    assert res.rows_flagged == 0
    assert res.anomaly_counts == {}
    assert res.verdict == "PASS"
    assert res.flagged_manifest is None
    # Round-trip the clean data back through the manifest.
    back = bulk.read(res.clean_manifest)
    assert back.num_rows == res.rows_clean == res.rows_total
    assert back.schema.field("ts").type == pa.int64()
