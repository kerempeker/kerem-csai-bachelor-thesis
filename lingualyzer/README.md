# Lingualyzer per-pair stimulus distinguishability

This folder is the **public archive of the linguistic stimulus-validation
analysis** referenced from Methods 3.3.3 and Appendix B of the thesis.
Everything the thesis cites as "the full per-pair table" lives here.

## Files

| File | What it is | Format |
|---|---|---|
| `ai_features_matrix.tsv` | Raw Lingualyzer output for the 20 AI-generated stimuli. One row per linguistic metric, one column per text. | TSV, 33 metrics × 20 texts |
| `human_features_matrix.tsv` | Raw Lingualyzer output for the 20 human-authored stimuli, same shape. | TSV, 33 metrics × 20 texts |
| `linguistic_results.json` | Aggregate-level summary: per-metric AI vs. human means, SDs, mean delta, and Cohen's *d*. | JSON list, 14 selected metrics |
| `per_pair_distinguishability.json` | Per-pair distinguishability summary: RMS *z*, max *z*, count of metrics at medium and large effect sizes, and the single most differentiating metric per pair. | JSON list, 20 pairs |
| `per_pair_lingualyzer.csv` | Tidy per-pair table merging TF-IDF cosine and bigram Jaccard from the similarity check with the Lingualyzer per-pair summary. | CSV, 20 rows × 10 columns |
| `per_pair_lingualyzer.md` | Same as the CSV, rendered as Markdown with column definitions. | Markdown |

## How the files relate

```
ai_features_matrix.tsv    ─┐
human_features_matrix.tsv ─┼─> per-pair z-scores ─> per_pair_distinguishability.json
                           └─> aggregate effects  ─> linguistic_results.json

similarity_check.py (TF-IDF cosine + bigram Jaccard)
                           └─> merged with per-pair summary ─> per_pair_lingualyzer.csv / .md
```

## What this measures

For each of the 20 topic pairs (one human-authored verbatim text + one
AI-generated counterpart from Claude Opus 4 at temperature 0.7,
keyword-only prompt):

- **TF-IDF cosine similarity** and **bigram Jaccard overlap** establish
  that the AI text is *not* a paraphrase of the human source.
- **Lingualyzer RMS *z* and max *z*** summarise the overall and
  worst-case standardised difference across 33 surface and linguistic
  complexity metrics.
- **n_medium_d / n_large_d** count the metrics on which the pair
  diverges at Cohen's *d* > 0.5 (medium) and > 0.8 (large).
- **top_diff_metric** is the single Lingualyzer metric on which the AI
  and human text differ the most within that pair.

The aggregate numbers reported in the thesis (mean cosine 0.41, mean
bigram 0.04, 24/33 metrics differing at small or larger effect sizes)
are the column-wise summaries of the files in this folder.

## Lingualyzer

Lingualyzer is a linguistic-analysis toolkit developed by Linders &
Louwerse (2023) at the Tilburg Cognitive Science and AI department.
The tool was used purely for descriptive stimulus validation; no
inferential test in the thesis depends on its output.
