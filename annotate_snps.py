"""Pulls public annotation for every SNP in snp_panel.json (scored panel, candidates, dropped)
from the Ensembl REST API and saves snp_annotation.csv.
Run:  python annotate_snps.py"""
import csv, json, time, requests

data = json.load(open("snp_panel.json"))
items = []
for s in data.get("panel", []):
    items.append(("panel", s["gene"], s["rsid"], s.get("risk_allele"), s.get("weight")))
for s in data.get("candidates", []):
    items.append(("candidate", s["gene"], s["rsid"], s.get("risk_allele"), 0))
for s in data.get("dropped", []):
    items.append(("dropped", s["gene"], s["rsid"], None, 0))

FIELDS = ["list", "gene", "rsid", "project_risk_allele", "project_weight", "alleles",
          "location_GRCh38", "minor_allele", "MAF", "consequence", "clinvar_significance", "status"]
rows = []
for lst, gene, rsid, ra, w in items:
    row = {"list": lst, "gene": gene, "rsid": rsid, "project_risk_allele": ra,
           "project_weight": w, "status": "ok"}
    try:
        r = requests.get(f"https://rest.ensembl.org/variation/human/{rsid}",
                         headers={"Content-Type": "application/json"}, timeout=30)
        r.raise_for_status()
        d = r.json()
        m = (d.get("mappings") or [{}])[0]
        row.update({
            "alleles": m.get("allele_string"),
            "location_GRCh38": f"{m.get('seq_region_name')}:{m.get('start')}",
            "minor_allele": d.get("minor_allele"), "MAF": d.get("MAF"),
            "consequence": d.get("most_severe_consequence"),
            "clinvar_significance": "; ".join(d.get("clinical_significance") or []) or "none listed",
        })
        print("OK  ", rsid)
    except Exception as e:
        row["status"] = f"failed: {e}"
        print("FAIL", rsid, e)
    rows.append(row)
    time.sleep(0.4)

with open("snp_annotation.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)
print("Saved snp_annotation.csv")
print("Note: Ensembl alleles are on the forward strand of GRCh38; compare with the allele coded in each paper.")
