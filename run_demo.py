import json
from phase_engine import recommend, PANEL

if any(s["weight"] > 0 and not s["verified"] for s in PANEL):
    print("WARNING: a scored SNP is not marked verified in snp_panel.json\n")

for p in json.load(open("patients.json")):
    r = recommend(p["genotypes"], p["fasting_insulin_uIU_mL"], p["cycle_day"], p["cycle_length"])
    print(p["id"]); print(json.dumps(r, indent=2)); print()

p = json.load(open("patients.json"))[0]
print("Day  phase             carb%")
for d in range(1, 29):
    r = recommend(p["genotypes"], p["fasting_insulin_uIU_mL"], d, 28)
    print(f"{d:>3}  {r['phase']:<16}  {r['carb_percent_of_energy']:>5}")
    
