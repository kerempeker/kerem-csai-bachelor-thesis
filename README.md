# Coding Component — Bachelor's Thesis

**Author:** Kerem Peker (ANR 2106332)
**Supervisor:** prof. dr. Max M. Louwerse
**Programme:** BSc Cognitive Science and Artificial Intelligence, Tilburg University
**Submission date:** 22 May 2026

This archive contains every piece of code written for the project
*"Detecting AI-Generated Political Statements: A Credibility Heuristic"*.
All scripts are documented for reproducibility and can be run independently.

## Folder structure

```
Code_Submission/
├── README.md                              ← this file
├── requirements.txt                       ← Python dependencies (pip)
├── R_packages.txt                         ← R dependencies (CRAN)
│
├── sample_data/
│   ├── thesis_trial_data.csv              ← long-format trial data (N=87, 1,740 rows)
│   └── README.md                          ← data dictionary
│
├── python_analysis/
│   ├── 01_extract_and_analyse.py          ← reads Qualtrics export, runs all H1–H5 stats
│   ├── 02_generate_figures.py             ← produces 9 publication-ready PNGs
│   ├── 03_generate_tables.py              ← produces Tables 1 & 2 as Word + CSV
│
├── R_analysis/
│   └── mixed_effects_and_robustness.R     ← clmm (mixed-effects ordinal) + Brant test
│                                             + Likert-3 robustness (4 codings)
│
├── stimuli/                              ← full 20-pair stimulus pool (AI + human .txt files)
└── example_outputs/
    ├── figures/   (fig1–fig9 PNGs as in the thesis)
    └── tables/    (table1, table2 as docx + csv)
```

## How to reproduce the full analysis

```bash
# 1.  Set up Python environment (3.13+)
pip install -r requirements.txt

# 2.  Set up R environment (4.5+)
Rscript -e 'install.packages(c("ordinal", "brant", "MASS"))'

# 3.  Run the analysis pipeline
cd python_analysis
python3 01_extract_and_analyse.py     # produces thesis_trial_data.csv + console stats
python3 02_generate_figures.py        # 9 PNGs in ../example_outputs/figures/
python3 03_generate_tables.py         # 2 tables in ../example_outputs/tables/

cd ../R_analysis
Rscript mixed_effects_and_robustness.R  # mixed-effects ordinal regression + Brant test

```

## What each script does

| File | Language | Purpose |
|---|---|---|
| `01_extract_and_analyse.py` | Python | Loads the Qualtrics CSV export, applies the duration-window quality filter, computes Wilcoxon signed-rank tests (H2, H3), an exact binomial test (H1), and four nested fixed-effects proportional-odds ordinal logistic regressions (H4, H5). Saves long-format trial-level data and a JSON summary. |
| `02_generate_figures.py` | Python | Produces all nine thesis figures with consistent APA-style typography (DejaVu Serif, 300 DPI, restrained palette). Figures: sample funnel, trial-structure schematic, accuracy distribution, confusion matrix, paired box plots, forest plot of ordinal coefficients, per-stimulus accuracy, Likert-3 robustness bar chart, predicted attribution probabilities. |
| `03_generate_tables.py` | Python | Refits the ordinal regressions and emits Table 1 (sample characteristics) and Table 2 (ordinal regression results) as standalone CSV and Word table snippets with hand-drawn borders. |
| `04_build_thesis_docx.py` | Python | Loads the official Tilburg BSc CSAI template, populates the title page, replaces the lorem-ipsum body, inserts subsections with bold labels and proper paragraph spacing, places figures and tables, and applies Heading 1 / Heading 2 styles for navigation. |
| `mixed_effects_and_robustness.R` | R | Fits a cumulative-link mixed model (`clmm`) with random intercepts for participant and stimulus — the principal inferential model in the thesis. Runs the Brant test for the proportional-odds assumption. Reports four alternative codings of the Likert-3 ("Not sure") response as a sensitivity analysis. |

## Code authorship and citations

All code in this archive was written by the author specifically for this thesis.
No third-party scripts were copied. Where standard library or package idioms
are used, the package is cited inline at the top of each file. The Lingualyzer
linguistic-analysis output cited in Methods 3.3 was produced by the publicly
available web tool maintained by the Tilburg CSAI department (Linders &
Louwerse, 2023); the raw Lingualyzer output is not included here since it is
documented in the thesis appendices and was not the subject of any custom code.


## Dependencies

**Python (3.13+)**
```
pandas >= 2.2
numpy >= 2.0
scipy >= 1.13
statsmodels >= 0.14
matplotlib >= 3.8
python-docx >= 1.1
```

**R (4.5+)**
```
ordinal >= 2025.12     # clmm() cumulative-link mixed models
brant >= 0.3-0          # Brant test for proportional odds
MASS >= 7.3             # polr() ordinal regression (Brant input)
```
