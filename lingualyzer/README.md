# Lingualyzer per-pair stimulus distinguishability

This folder contains the **full per-pair table** referenced from
Methods 3.3.3 and Appendix B of the thesis.

## Files

| File | What it is |
|---|---|
| `per_pair_lingualyzer.csv` | Tidy table, one row per stimulus pair (20 rows × 10 columns). |
| `per_pair_lingualyzer.md` | Same table in Markdown, plus column definitions. |
| `per_pair_distinguishability_raw.json` | Raw Lingualyzer output (per-pair z-scores on all 33 metrics, including top differentiators per pair). |

## What this measures

For each of the 20 topic pairs (one human-authored verbatim text + one
AI-generated counterpart from Claude Opus 4):

- **TF-IDF cosine similarity** and **bigram Jaccard overlap** — establish
  that the AI text is *not* a paraphrase of the human source.
- **Lingualyzer RMS z and max z** — overall and worst-case standardised
  difference across 33 surface and linguistic-complexity metrics.
- **n_medium_d / n_large_d** — count of metrics on which the pair
  diverges at Cohen's *d* > 0.5 / > 0.8.
- **top_diff_metric** — the single Lingualyzer metric on which the AI and
  human text differ the most for that pair.

The aggregate numbers reported in the thesis (mean cosine 0.41, mean
bigram 0.04, 24/33 metrics differing) are the column-wise summaries of
the table in this folder.

## Lingualyzer

Lingualyzer is a linguistic-analysis toolkit developed by Linders &
Louwerse (2023) at the Tilburg Cognitive Science and AI department.
The tool was used purely for descriptive stimulus validation; no
inferential test in the thesis depends on its output.
