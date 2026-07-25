"""H-004 config sanity (ARCH-009 §4.3) — the sealed pre-registration values.

Guards the pre-registered H-004 YAML against silent drift: multi-window (two
window_refs), the DEVQ-019 calendar exit, the sealed placebo_method, min_n = 45
(DEVQ-022 Q2), and the DEVQ-011 embargo >= hold + 1 boundary rule. A shape check
only (no store): editing any field must be a DELIBERATE re-registration, and this
test makes an accidental edit to the sealed numbers loud.
"""

from __future__ import annotations

from qrf.kernel.protocol.hypotheses import HypothesisRegistry

H004 = "configs/hypotheses/h004_dow_monday_drift_v2.yaml"


def _cfg():
    return HypothesisRegistry.load_config(H004)


def test_multi_window_two_disjoint_spans():
    cfg = _cfg()
    assert "window" not in cfg  # multi-window uses window_refs, never a single window
    assert isinstance(cfg["window_refs"], list) and len(cfg["window_refs"]) == 2
    # the 2024-training then the 2025-training window, in seam order.
    assert cfg["window_refs"][0] == "01KYB4SSC96SSS8RA7D1NMTPEX"
    assert cfg["window_refs"][1] == "01KYDE784029NZNXPPN5PA8P8G"


def test_calendar_exit_sealed():
    cfg = _cfg()
    assert cfg["execution"]["exit_rule"] == "calendar_day"
    assert cfg["setup_dsl"]["exit"] == "calendar_same_dow"


def test_placebo_method_sealed_entry_time_shuffle():
    assert _cfg()["placebo_method"] == "entry_time_shuffle"


def test_min_n_is_devq022_ratified_45():
    assert _cfg()["thresholds"]["min_n"] == 45


def test_embargo_clears_hold_plus_one():
    cfg = _cfg()
    hold = cfg["execution"]["hold_bars"]
    embargo = cfg["split_spec"]["embargo_bars"]
    assert embargo >= hold + 1  # DEVQ-011 BINDING boundary-gap rule


def test_v2_precommitments_and_interpretation_guard():
    cfg = _cfg()
    assert cfg["family"] == "xauusd_h1/seasonality.calendar"
    interp = cfg["outcome_interpretations"]
    assert set(interp) == {"PASS", "FAIL", "INSUFFICIENT"}
    # OBS-1 interpretation guard: PASS claims "beats random timing", not "profitable".
    assert "random" in interp["PASS"].lower()
