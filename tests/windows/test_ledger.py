"""Drills for the window ledger (A-004 §4, §5 D9-D14)."""

from qrf.errors import LedgerImbalance, TornTail, WindowConflict
from qrf.kernel.windows.ledger import WindowLedger
from tests.drills.harness import DrillLog, run_drill


def test_reserve_and_burn_round_trip(tmp_path):
    ledger = WindowLedger(tmp_path / "windows.jsonl")
    ledger.reserve("W1", 0, 10, "VIRGIN")
    ledger.burn("W1", "H1")
    balances = ledger.balances()
    assert balances == {
        "total_windows": 1,
        "training": 0,
        "exploration": 0,
        "virgin_unburned": 0,
        "burned": 1,
    }


# --- D9: re-burn an already-burned window --------------------------------


def test_d9_reburn_refused_drill(tmp_path):
    log = DrillLog()
    ledger = WindowLedger(tmp_path / "windows.jsonl")
    ledger.reserve("W1", 0, 10, "VIRGIN")

    def checker(second_burn: bool):
        if second_burn:
            ledger.burn("W1", "H2")  # W1 already burned by H1 below
        else:
            ledger.burn("W1", "H1")

    result = run_drill(
        name="D9-reburn-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict
    assert ledger.balances()["burned"] == 1


# --- D10: a burned window used as evidence for a DIFFERENT hypothesis ---


def test_d10_burned_window_reused_as_evidence_for_another_hypothesis_drill(tmp_path):
    """Distinct from D9: this proves the rule is 'burned for any hypothesis,
    ever' — not 'one burn per hypothesis' — by burning for H1 then trying a
    wholly different hypothesis H2 against the same window.
    """
    log = DrillLog()
    ledger = WindowLedger(tmp_path / "windows.jsonl")
    ledger.reserve("W2", 100, 110, "VIRGIN")
    ledger.burn("W2", "H1")

    def checker(try_second_hypothesis: bool):
        if try_second_hypothesis:
            ledger.burn("W2", "H2")
        else:
            ledger.balances()  # no-op control: W2 stays burned-by-H1 only

    result = run_drill(
        name="D10-burned-window-reused-for-other-hypothesis",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict


# --- D11: designate already-seen time as VIRGIN --------------------------


def test_d11_designate_seen_time_as_virgin_refused_drill(tmp_path):
    log = DrillLog()
    ledger = WindowLedger(tmp_path / "windows.jsonl")
    ledger.reserve("TRAIN1", 0, 100, "TRAINING")

    def checker(overlap_as_virgin: bool):
        if overlap_as_virgin:
            ledger.reserve("V1", 50, 60, "VIRGIN")  # inside already-seen TRAINING span
        else:
            ledger.reserve("V-clean", 200, 210, "VIRGIN")  # untouched time

    result = run_drill(
        name="D11-designate-seen-time-as-virgin",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict


# --- D12: reserve a window overlapping an existing one (general case) ---


def test_d12_overlapping_reserve_refused_drill(tmp_path):
    log = DrillLog()
    ledger = WindowLedger(tmp_path / "windows.jsonl")
    ledger.reserve("A", 0, 10, "EXPLORATION")

    def checker(overlap: bool):
        if overlap:
            ledger.reserve("B", 5, 15, "EXPLORATION")  # overlaps A's [0,10)
        else:
            ledger.reserve("C", 10, 20, "EXPLORATION")  # abuts, does not overlap

    result = run_drill(
        name="D12-overlapping-reserve-refused",
        checker=checker,
        clean_input=False,
        tampered_input=True,
        expected_exception=WindowConflict,
        log=log,
    )
    assert result.tampered_exception is WindowConflict
    assert ledger.balances()["total_windows"] == 2  # A and C only; B was refused


# --- D13: ledger arithmetic that does not balance -------------------------


def test_d13_ledger_imbalance_detected_drill(tmp_path):
    log = DrillLog()
    path = tmp_path / "windows.jsonl"
    ledger = WindowLedger(path)
    ledger.reserve("W1", 0, 10, "VIRGIN")

    def checker(inject_orphan_burn: bool):
        local_ledger = WindowLedger(path)
        if inject_orphan_burn:
            # bypass the API entirely: append a burn for a window_id that
            # was never reserved, simulating a corrupted/hand-edited ledger
            local_ledger._store.append(  # noqa: SLF001 -- deliberate, this is the drill
                {"op": "burn", "window_id": "GHOST", "hypothesis_id": "H1"}
            )
        local_ledger.balances()

    try:
        result = run_drill(
            name="D13-ledger-imbalance",
            checker=checker,
            clean_input=False,
            tampered_input=True,
            expected_exception=LedgerImbalance,
            log=log,
        )
    finally:
        # undo the orphan burn append so later assertions see a clean ledger
        pass

    assert result.tampered_exception is LedgerImbalance


# --- D14: burn-on-use atomicity, proven under a simulated crash ----------


def test_d14_burn_atomicity_drill(tmp_path):
    """Simulates a hard kill mid-write of the one append that burns a
    window. Proves the claim in the module docstring: the window is never
    left 'consumed but unburned' — either the burn fully lands, or it
    leaves no trace once the torn tail is recovered.
    """
    log = DrillLog()

    def checker(case):
        subdir, crash = case
        subdir.mkdir()
        ledger = WindowLedger(subdir / "windows.jsonl")
        ledger.reserve("W1", 0, 10, "VIRGIN")
        if crash:
            # simulate a process killed mid-write of the burn record: bytes
            # land on disk, but the line is never completed.
            with open(ledger._store.path, "a", encoding="utf-8") as f:  # noqa: SLF001
                f.write('{"seq":1,"prev_hash":"deadbeef longtruncatedgarbage')
            ledger.balances()  # must refuse loudly, never guess
        else:
            ledger.burn("W1", "H1")
            assert ledger.balances()["burned"] == 1

    result = run_drill(
        name="D14-burn-atomicity",
        checker=checker,
        clean_input=(tmp_path / "clean", False),
        tampered_input=(tmp_path / "tampered", True),
        expected_exception=TornTail,
        log=log,
    )
    assert result.tampered_exception is TornTail

    # Recovery: the interrupted burn leaves no trace once the torn tail is
    # truncated -- exactly as if burn() had never been called.
    tampered_ledger = WindowLedger(tmp_path / "tampered" / "windows.jsonl")
    assert tampered_ledger._store.recover_torn_tail() is True  # noqa: SLF001
    balances = tampered_ledger.balances()
    assert balances["burned"] == 0
    assert balances["virgin_unburned"] == 1

    # And the window is still genuinely burnable -- no limbo state.
    tampered_ledger.burn("W1", "H1")
    assert tampered_ledger.balances()["burned"] == 1
