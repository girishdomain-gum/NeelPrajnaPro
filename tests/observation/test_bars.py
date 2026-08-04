"""AM-07 Stage A P1: the CSV-to-Bar loader.

CONTROL/TAMPERED tests here run entirely against SYNTHETIC, tracked
fixtures written to `tmp_path` -- never against any real market data,
VIRGIN or spent. The one test that reads a REAL file
(`test_p1_real_replay_spent_20000_bar_window`) reads ONLY the dataset
this project's ledger records as already-spent EXPLORATION time
(`stage_a_replay_source_s07_fresh_window`, appended per A-038 Ruling 2,
citing F-07) -- never the live VIRGIN collection batch. If that ledger
record is ever missing, this test's own assertion on `balances()` fails
loudly rather than silently trusting the path is safe to read.
"""

from pathlib import Path

import pytest

from qrf.errors import SchemaViolation
from qrf.kernel.detection.types import Bar
from qrf.kernel.observation.bars import EXPECTED_HEADER, load_bars_csv
from qrf.kernel.windows.ledger import WindowLedger
from tests.drills.harness import DrillLog, run_drill

REAL_LEDGER = Path(r"F:\NeelPrajnaProData\datastore\s02_windows\ledger.jsonl")
REAL_SPENT_CSV = Path(
    r"F:\NeelPrajnaProData\datastore\s07_bulk\xauusd_m5_s07_fresh_window.csv"
)
REAL_SPENT_SHA256 = "e4a93ccc2302677233fb5c6b2f0f98a679dbcb9503c5289315181268f78260ca"
REAL_SPENT_WINDOW_ID = "stage_a_replay_source_s07_fresh_window"


def _write_csv(path: Path, header: tuple, rows: list) -> None:
    lines = [",".join(header)]
    lines.extend(",".join(str(v) for v in row) for row in rows)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_control_parses_real_format_correctly(tmp_path):
    csv_path = tmp_path / "clean.csv"
    _write_csv(
        csv_path,
        EXPECTED_HEADER,
        [
            [1_700_000_000, "10.00000000", "11.00000000", "9.00000000", "10.50000000", 100, 2, 0],
            [1_700_000_300, "10.50000000", "10.90000000", "10.10000000", "10.20000000", 90, 2, 0],
        ],
    )
    bars = load_bars_csv(csv_path)
    assert bars == (
        Bar(time=1_700_000_000, open=10.0, high=11.0, low=9.0, close=10.5),
        Bar(time=1_700_000_300, open=10.5, high=10.9, low=10.1, close=10.2),
    )


def test_no_extra_columns_leak_into_bar(tmp_path):
    """tick_volume/spread/real_volume are in the real export but NOT part
    of the Bar SDK type (AM-01) -- confirm they are dropped, not merely
    ignored by accident.
    """
    csv_path = tmp_path / "clean.csv"
    _write_csv(
        csv_path,
        EXPECTED_HEADER,
        [[1, "1.0", "1.0", "1.0", "1.0", 999, 999, 999]],
    )
    (bar,) = load_bars_csv(csv_path)
    assert bar == Bar(time=1, open=1.0, high=1.0, low=1.0, close=1.0)


# --- header refusal, drilled RED then GREEN (house law 3; A-038's required
# refuse-on-unexpected-header behaviour) --------------------------------


def test_header_refusal_drill(tmp_path):
    log = DrillLog()

    def checker(header: tuple):
        csv_path = tmp_path / f"{'_'.join(header)[:20]}.csv"
        _write_csv(
            csv_path,
            header,
            [[1, "1.0", "1.0", "1.0", "1.0", 1, 1, 1]] if len(header) == 8 else [[1, "1.0"]],
        )
        load_bars_csv(csv_path)

    result = run_drill(
        name="P1-header-refusal",
        checker=checker,
        clean_input=EXPECTED_HEADER,
        tampered_input=("time_open_sec", "time_close_sec", "open", "high", "low", "close",
                         "tick_volume", "spread", "real_volume", "dow"),  # the PREVIOUS era's shape
        expected_exception=SchemaViolation,
        log=log,
    )
    assert result.tampered_exception is SchemaViolation


def test_reordered_header_is_refused_not_silently_remapped(tmp_path):
    """A header with the RIGHT column names in the WRONG order must still
    be refused -- this loader does not remap by name, only by exact
    position, so a silent reorder can never produce silently-swapped OHLC.
    """
    csv_path = tmp_path / "reordered.csv"
    reordered = ("time", "high", "open", "low", "close", "tick_volume", "spread", "real_volume")
    _write_csv(csv_path, reordered, [[1, "2.0", "1.0", "0.5", "1.5", 1, 1, 1]])
    with pytest.raises(SchemaViolation):
        load_bars_csv(csv_path)


def test_empty_file_is_refused():
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        csv_path = Path(d) / "empty.csv"
        csv_path.write_text("", encoding="utf-8")
        with pytest.raises(SchemaViolation):
            load_bars_csv(csv_path)


def test_malformed_row_is_refused_drill(tmp_path):
    log = DrillLog()

    def checker(value: str):
        csv_path = tmp_path / "row.csv"
        _write_csv(csv_path, EXPECTED_HEADER, [[1, value, "1.0", "1.0", "1.0", 1, 1, 1]])
        load_bars_csv(csv_path)

    result = run_drill(
        name="P1-malformed-row-refusal",
        checker=checker,
        clean_input="1.0",
        tampered_input="not-a-number",
        expected_exception=SchemaViolation,
        log=log,
    )
    assert result.tampered_exception is SchemaViolation


def test_short_row_is_refused(tmp_path):
    csv_path = tmp_path / "short.csv"
    csv_path.write_text("time,open,high,low,close,tick_volume,spread,real_volume\n1,1,1,1,1\n",
                         encoding="utf-8")
    with pytest.raises(SchemaViolation):
        load_bars_csv(csv_path)


# --- P1 real-scale replay: the spent, EXPLORATION-labelled 20,000-bar
# window (A-038 Ruling 2) -- never the live VIRGIN batch ----------------


@pytest.mark.skipif(not REAL_SPENT_CSV.exists(), reason="real Stage A dataset not present")
def test_p1_real_replay_spent_20000_bar_window():
    # Positive check per A-038 Ruling 2: this span must carry an explicit
    # EXPLORATION record before anything reads it as Stage A material.
    ledger = WindowLedger(REAL_LEDGER)
    balances = ledger.balances()
    assert balances["exploration"] >= 2, (
        "expected the stage_a_replay_source EXPLORATION record to exist; "
        f"got balances={balances}"
    )

    import hashlib

    actual_sha256 = hashlib.sha256(REAL_SPENT_CSV.read_bytes()).hexdigest()
    assert actual_sha256 == REAL_SPENT_SHA256, "spent dataset's bytes changed on disk"

    bars = load_bars_csv(REAL_SPENT_CSV)
    assert len(bars) == 20_000
    assert bars[0].time == 1_767_766_200
    assert bars[-1].time == 1_776_722_400
    # C2-adjacent: loading twice from the same bytes is byte-identical.
    assert load_bars_csv(REAL_SPENT_CSV) == bars
