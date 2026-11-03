"""Cycle-synced nutrition engine. EXPLORATORY prototype, not a clinical tool.
Reads snp_panel.json and parameters.json."""
import json, math
from pathlib import Path

BASE = Path(__file__).parent
PANEL = json.loads((BASE / "snp_panel.json").read_text())["panel"]
PARAMS = json.loads((BASE / "parameters.json").read_text())

MIN_CYCLE, MAX_CYCLE = 21, 45
LUTEAL_LENGTH = 14  # assumption: next period ~14 days after ovulation
PHASE_BASIS = "calendar-based estimate from cycle day and length; ovulation not confirmed"


def estimated_ovulation_day(cycle_length):
    return cycle_length - LUTEAL_LENGTH


def get_phase(day, cycle_length=None):
    """Return a phase name, or 'insufficient_data' if day or cycle length is missing/implausible."""
    if day is None or cycle_length is None or not (MIN_CYCLE <= cycle_length <= MAX_CYCLE):
        return "insufficient_data"
    if not 1 <= day <= cycle_length:
        raise ValueError(f"cycle_day must be between 1 and {cycle_length}")
    ov = estimated_ovulation_day(cycle_length)
    if day <= 5:
        return "menstrual"
    if day < ov - 2:
        return "early_follicular"
    if day < ov:
        return "late_follicular"
    if day == ov:
        return "ovulation"
    return "luteal"


def luteal_pressure(day, cycle_length):
    """Smooth 0..1 curve, 0 outside the luteal phase, peaking mid-luteal (progesterone stand-in)."""
    if get_phase(day, cycle_length) != "luteal":
        return 0.0
    ov = estimated_ovulation_day(cycle_length)
    return math.sin(math.pi * (day - ov) / (cycle_length - ov + 1))


def _valid(g):
    return isinstance(g, str) and len(g) == 2 and g.isalpha()


def genetic_score(genotypes):
    """Weighted share of risk alleles (0..1) over SNPs with weight > 0 and a usable genotype.
    Missing genotypes are never treated as risk. Returns None if no scored SNP has data."""
    num = den = 0.0
    used, zero_weight, missing = [], [], []
    for s in PANEL:
        rs, ra, w = s["rsid"], s["risk_allele"], s.get("weight") or 0.0
        if ra is None or w <= 0:
            zero_weight.append(rs)
            continue
        g = genotypes.get(rs)
        if not _valid(g):
            missing.append(rs)
            continue
        num += w * g.upper().count(ra.upper()) / 2
        den += w
        used.append(rs)
    score = round(num / den, 3) if den else None
    status = "none" if not used else ("partial" if missing else "complete")
    return score, used, zero_weight, missing, status


def recommend(genotypes, fasting_insulin=None, cycle_day=None, cycle_length=None):
    p = PARAMS
    score, used, zero_w, missing, status = genetic_score(genotypes or {})
    phase = get_phase(cycle_day, cycle_length)

    if phase == "insufficient_data":
        lp, phase_factor = None, 1.0  # static default: full genetic weight, no phase scaling (assumption)
    else:
        lp = luteal_pressure(cycle_day, cycle_length)
        phase_factor = 0.3 + 0.7 * lp

    eff = (score or 0.0) * phase_factor
    carb = p["base_carb_pct"] - p["max_carb_reduction_pct"] * eff

    thr = p.get("high_insulin_uIU_mL")
    high_ins = None
    if thr is not None and fasting_insulin is not None:
        high_ins = fasting_insulin > thr
        if high_ins:
            carb -= p["insulin_extra_carb_reduction_pct"]
    carb = min(p["base_carb_pct"], max(p["carb_floor_pct"], carb))

    return {
        "phase": phase,
        "phase_estimate_basis": PHASE_BASIS if phase != "insufficient_data" else "none (missing cycle data; static default used)",
        "cycle_day": cycle_day,
        "luteal_pressure_0to1": None if lp is None else round(lp, 2),
        "genetic_risk_score_0to1": score,
        "genetic_data_status": status,
        "snps_scored": used,
        "snps_not_scored": zero_w,
        "snps_missing_genotype": missing,
        "carb_percent_of_energy": round(carb, 1),
        "fiber_g_per_day": round(p["base_fiber_g"] + p["max_extra_fiber_g"] * eff),
        "protein_g_per_kg": round(p["base_protein_g_per_kg"] + p["max_extra_protein_g_per_kg"] * eff, 2),
        "high_fasting_insulin": high_ins,
        "heuristic_fields": ["carb_percent_of_energy (genotype x phase adjustment is an exploratory product rule)"],
        "evidence_status": "Only the 45% base carb figure is literature-anchored (PMID 31885557). Fiber and protein are general adult references. Guidelines recommend no specific diet composition (PMID 32452622).",
        "disclaimer": "Exploratory prototype. Not medical advice or a validated risk calculator.",
      }
  
