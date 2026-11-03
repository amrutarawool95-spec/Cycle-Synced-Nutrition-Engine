# Cycle-Synced Nutrition Engine (Exploratory Prototype)

A small Python project that explores adjusting carbohydrate targets across the menstrual cycle, using a genetic risk score and the estimated cycle phase. Built with PCOS in mind.

> **Exploratory prototype. Not a medical device, not a validated risk calculator, and not advice.** Phase-specific macronutrient targets are not clinically established. Guidelines recommend no specific diet composition for PCOS.

## What is evidence-based and what is not

| Part | Status |
|---|---|
| 45% energy carbohydrate base value | From a source (PMID 31885557, 8 RCTs in PCOS). A study definition, not a universal target |
| Fiber 25 g/day, protein 0.8 g/kg/day | General adult references (DRI/RDA), not PCOS-specific |
| Carb reduction by genotype and phase | **Exploratory product rule, no supporting study** |
| Insulin / HOMA-IR cutoff | None. No universal cutoff is supported, so the threshold is `null` |
| Cycle phase | Calendar-based estimate. Ovulation is estimated at (cycle length - 14), not confirmed |

## How it works

1. **Genetic score (0 to 1):** share of risk alleles over SNPs that have a weight above 0 and a usable genotype. Missing or invalid genotypes are never treated as risk.
2. **Cycle phase:** menstrual, early follicular, late follicular, ovulation or luteal, from `cycle_day` and `cycle_length`. If either is missing, the phase is `insufficient_data` and a static default is used.
3. **Luteal pressure (0 to 1):** a smooth curve, 0 outside the luteal phase, peaking mid-luteal.
4. **Output:** carbs go down from 45% toward a 35% floor as score and luteal pressure rise. Fiber and protein stay at general adult references.

## SNP decisions

| SNP | In score? | Reason |
|---|---|---|
| PPARG rs1801282 (risk allele C) | Yes (single scored SNP) | G (Ala) protective across meta-analyses (PMID 22527903, 22564702, 23748472). Weight 1.0 is a normalisation, not an effect size |
| FTO rs9939609 (A, provisional) | No (weight 0) | Not replicated in Indian samples (Gujarat n=114, South India n=170), largely BMI-mediated, papers conflict on allele direction |
| INSR rs1799817 (T) | No (weight 0) | Dominant-model, lean-subgroup, population-specific evidence. Mixed results (Kashmiri, South Indian nulls) |
| INSR rs2059807 | No | Strand/notation differs between papers. Risk allele not assigned |
| TPH2 rs4570625 | Dropped | No convincing PCOS paper found |
| ESR1 rs2234693, rs9340799 | Dropped | Meta-analysis null (PMID 34671317) |
| KISS1 rs4889, rs372790354 | Candidates only | From PMID 39126595, mapping not confirmed |

Allele frequency (gnomAD v4.1.2, FTO A allele): global 0.41, South Asian 0.31, East Asian 0.15.

Full evidence, conflicts and PMIDs are in `snp_panel.json`.

## Project files

| File | What it does |
|---|---|
| `phase_engine.py` | Phase estimate, luteal pressure, genetic score, recommendation |
| `snp_panel.json` | SNP evidence catalogue with weights, models, conflicts |
| `parameters.json` | Engine values, each with provenance (sourced, general reference or assumption) |
| `parameters_evidence.json` | Literature evidence on carbohydrate intake, with PMIDs |
| `patients.json` | Synthetic test patients |
| `run_demo.py` | Runs the patients and prints a day 1-28 table |
| `annotate_snps.py` | Fetches public SNP info from Ensembl into `snp_annotation.csv` |
| `api.py` | FastAPI endpoint `POST /recommend` |
| `tests/test_engine.py` | 18 tests for phase mapping and rule behaviour |
| `requirements.txt` | Python packages |

## Quick start

```bash
git clone https://github.com/amrutarawool95-spec/Cycle-Synced-Nutrition-Engine.git
cd Cycle-Synced-Nutrition-Engine
pip install -r requirements.txt
python run_demo.py
python -m pytest
```

On a phone, upload the files to [Google Colab](https://colab.research.google.com) and run `!pip install -q -r requirements.txt` then `!python run_demo.py`.

API: `uvicorn api:app --reload`, then open `http://127.0.0.1:8000/docs` and use **POST /recommend**.

```json
{"genotypes": {"rs1801282": "CG"}, "cycle_day": 22, "cycle_length": 28}
```

## What the tests do and do not show

The tests check that the code follows its own rules (for example, high risk gives lower carbs than matched low risk, missing data is not high risk, zero-weight SNPs change nothing). They do **not** show that the rules are clinically valid.

## Limitations

- The genotype x phase carb adjustment has no supporting study.
- The luteal curve is a stand-in for progesterone, not measured hormones.
- Ovulation timing is often unpredictable in PCOS, so calendar phases can be wrong.
- Only one SNP is scored. SNP effects are small, population-dependent and often BMI-mediated.
- Additive allele counting is an assumption.
- Test patients are synthetic. Nothing is validated against clinical outcomes.

## Roadmap

- [x] FTO, INSR, PPARG, ESR1, TPH2 evidence reviewed
- [x] Tests for phase mapping and rule behaviour
- [ ] Confirm unverified PMIDs (e.g. PPARG 26770332, Gujarat and Saudi INSR papers)
- [ ] Normalise strand and build for INSR rs2059807
- [ ] Biomarker-based phase detection for irregular cycles (BBT, HRV)
- [ ] Streamlit page with a 28-day chart
- [ ] Regional adiposity module (Concept 2)

## Disclaimer

For research and education only. Please consult a qualified professional for health decisions.

## Author

**Amruta Rawool**
[LinkedIn](https://linkedin.com/in/amruta-rawool-59922a281) · [GitHub](https://github.com/amrutarawool95-spec)

## License

MIT (add a `LICENSE` file when you publish).
