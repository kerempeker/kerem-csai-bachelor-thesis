# Sample data — `thesis_trial_data.csv`

Long-format trial-level dataset produced by `01_extract_and_analyse.py` from
the raw Qualtrics export. One row per (participant × trial); 87 participants
× 20 trials = **1,740 rows**.

## Column dictionary

| Column        | Type    | Description |
|---------------|---------|-------------|
| `rid`         | string  | Anonymous Qualtrics response ID |
| `set`         | A / B   | Counterbalanced stimulus set assignment |
| `trial`       | 1–20    | Trial number (topic index) |
| `truth`       | AI / Human | True source of the stimulus on this trial |
| `truth_AI`    | 0 / 1   | Dummy: 1 if `truth == "AI"`, 0 otherwise |
| `attr`        | 1–5     | Participant's source-attribution rating (Likert: 1 = Definitely AI ... 5 = Definitely Human) |
| `fluency`     | 1–7     | Mean of the 5 Graf et al. (2018) fluency items for this trial |
| `credibility` | 1–7     | Mean of the 3 Appelman & Sundar (2016) credibility items for this trial |
| `p_ai_subj`   | 0.0–1.0 | Linear remap of `attr`: 1 → 1.0 ... 5 → 0.0 (subjective probability of AI authorship) |
| `brier`       | 0.0–1.0 | `(p_ai_subj − truth_AI)²` — squared error of the subjective probability against the true label |

## Provenance

- Survey instrument: deposited on OSF; details in thesis Appendix B (Source-verification audit).
- Raw export: `Reading Political Statements: A Cognitive Study for Thesis_<date>.csv` (Qualtrics download).
- Quality filter: `Finished == True` AND duration between 180 s and 3600 s.
- All participant identifiers are anonymous Qualtrics `ResponseId` strings; no demographic identifiers are linked.
