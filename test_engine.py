import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest
from phase_engine import get_phase, luteal_pressure, genetic_score, recommend, PARAMS

HIGH = {"rs1801282": "CC"}
LOW = {"rs1801282": "GG"}

# ---- cycle phase mapping ----
def test_day1_is_menstrual():
    assert get_phase(1, 28) == "menstrual"

@pytest.mark.parametrize("length,days", [(28, (12, 13)), (32, (16, 17))])
def test_late_follicular_before_ovulation(length, days):
    for d in days:
        assert get_phase(d, length) == "late_follicular"

@pytest.mark.parametrize("length,ov", [(28, 14), (32, 18)])
def test_ovulation_day_and_after(length, ov):
    assert get_phase(ov, length) == "ovulation"
    assert get_phase(ov + 1, length) == "luteal"
    assert get_phase(length, length) == "luteal"   # last day before next period

def test_ovulation_not_hardcoded_to_day_14():
    assert get_phase(14, 32) != "ovulation"
    assert get_phase(18, 32) == "ovulation"

def test_missing_cycle_data_is_insufficient():
    assert get_phase(None, 28) == "insufficient_data"
    assert get_phase(10, None) == "insufficient_data"
    r = recommend(HIGH)
    assert r["phase"] == "insufficient_data"
    assert r["luteal_pressure_0to1"] is None

def test_phase_output_is_labelled_as_estimate():
    assert "estimate" in recommend(HIGH, cycle_day=10, cycle_length=28)["phase_estimate_basis"]

def test_day_outside_cycle_raises():
    with pytest.raises(ValueError):
        get_phase(30, 28)

def test_luteal_pressure_zero_before_luteal():
    assert luteal_pressure(5, 28) == 0.0

# ---- risk-based carbohydrate rule (verifies the coded rule, not clinical validity) ----
def test_high_risk_gets_lower_carb_than_low_risk_same_inputs():
    hi = recommend(HIGH, None, 22, 28)["carb_percent_of_energy"]
    lo = recommend(LOW, None, 22, 28)["carb_percent_of_energy"]
    assert hi < lo

def test_carb_within_bounds():
    for d in range(1, 29):
        c = recommend(HIGH, 20.0, d, 28)["carb_percent_of_energy"]
        assert PARAMS["carb_floor_pct"] <= c <= PARAMS["base_carb_pct"]

def test_missing_snp_is_not_high_risk():
    r = recommend({}, None, 22, 28)
    assert r["genetic_risk_score_0to1"] is None
    assert r["genetic_data_status"] == "none"
    assert r["carb_percent_of_energy"] == PARAMS["base_carb_pct"]

def test_invalid_genotype_treated_as_missing():
    assert genetic_score({"rs1801282": "C"})[0] is None

def test_unsupported_snp_does_not_change_score():
    a = recommend(HIGH, None, 22, 28)
    b = recommend({**HIGH, "rs0000000": "AA"}, None, 22, 28)
    assert a["carb_percent_of_energy"] == b["carb_percent_of_energy"]

def test_zero_weight_snp_does_not_change_recommendation():
    a = recommend({**HIGH, "rs9939609": "AA"}, None, 22, 28)
    b = recommend({**HIGH, "rs9939609": "TT"}, None, 22, 28)
    assert a["carb_percent_of_energy"] == b["carb_percent_of_energy"]
    assert "rs9939609" in a["snps_not_scored"]

def test_output_flags_heuristic():
    r = recommend(HIGH, None, 22, 28)
    assert r["heuristic_fields"] and "evidence_status" in r

def test_no_universal_insulin_threshold():
    assert PARAMS["high_insulin_uIU_mL"] is None
    assert recommend(HIGH, 99.0, 22, 28)["high_fasting_insulin"] is None
