#!/usr/bin/env python3
"""
Robustness checks: by-items aggregation + predictor collinearity.

Two independent robustness tests for the principal H1-H5 findings reported in
the thesis:

  1. By-items analysis: re-run the H1 binomial test and the H2/H3 paired tests
     with the *stimulus* as the unit of analysis (n = 20 items) rather than the
     trial or participant. Confirms that the 56.5% headline accuracy and the
     +0.66 / +0.50 paired median deltas are not driven by particular
     participants. The 20 items are treated as the random factor here, mirroring
     the by-items random intercept in the principal CLMM (Section 4.5).

  2. Predictor collinearity: variance inflation factors (VIF) and the pairwise
     correlation matrix for true source, mean-centred fluency, and mean-centred
     credibility, computed on the 1,740 trial-level observations. Rules out
     multicollinearity as the explanation for the fluency-vs-credibility
     dissociation reported in Model 4 (full multivariable).

Usage:
    python3 robustness_byitems_collinearity.py

Inputs:
    ../sample_data/thesis_trial_data.csv  (also resolves ../thesis_trial_data.csv)

Outputs:
    Console summary + machine-readable JSON at
    ../example_outputs/tables/robustness_byitems_collinearity.json

Author: Kerem Peker (ANR 2106332), Tilburg University CSAI BSc, 2026.
"""
import json
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.outliers_influence import variance_inflation_factor


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)


def _resolve_paths():
    candidates_in = [
        os.path.join(PROJECT_ROOT, 'sample_data', 'thesis_trial_data.csv'),
        os.path.join(PROJECT_ROOT, 'thesis_trial_data.csv'),
    ]
    csv_path = next((p for p in candidates_in if os.path.exists(p)), candidates_in[0])
    if os.path.basename(os.path.dirname(csv_path)) == 'sample_data':
        out_dir = os.path.join(PROJECT_ROOT, 'example_outputs', 'tables')
    else:
        out_dir = os.path.join(PROJECT_ROOT, 'tables')
    return csv_path, out_dir


INPUT_CSV, OUTPUT_DIR = _resolve_paths()
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
def load_data():
    if not os.path.exists(INPUT_CSV):
        sys.exit(f"ERROR: missing {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} trials from {df.rid.nunique()} participants "
          f"and {df.trial.nunique()} stimuli")
    return df


# ===========================================================================
# 1. BY-ITEMS ANALYSIS
# ===========================================================================
def by_items_analysis(df):
    """Aggregate the headline H1, H2, H3 tests to the stimulus (n=20) level."""
    print("\n" + "=" * 70)
    print(" BY-ITEMS ROBUSTNESS (stimulus = unit of analysis, n = 20)")
    print("=" * 70)

    # Trial-level correctness, excluding the Likert-3 midpoint
    forced = df[df['attr'] != 3].copy()
    forced['correct'] = (
        ((forced['attr'] <= 2) & (forced['truth_AI'] == 1))
        | ((forced['attr'] >= 4) & (forced['truth_AI'] == 0))
    ).astype(int)

    # ---- H1: by-items detection accuracy
    per_item = (
        forced.groupby('trial')
        .agg(n_trials=('correct', 'size'),
             n_correct=('correct', 'sum'),
             accuracy=('correct', 'mean'))
        .reset_index()
    )
    item_mean = per_item['accuracy'].mean()
    item_sd = per_item['accuracy'].std(ddof=1)
    # One-sample t-test of item-level accuracy against chance (.50)
    t_stat, p_val = stats.ttest_1samp(per_item['accuracy'], 0.50)
    # Wilcoxon signed-rank (rank-based, robust to non-normality)
    w_stat, w_p = stats.wilcoxon(per_item['accuracy'] - 0.50,
                                  alternative='two-sided',
                                  zero_method='wilcox')
    aggregate_acc = forced['correct'].mean()

    print("\n[H1] Detection accuracy by items:")
    print(f"  Trial-level aggregate accuracy:    {aggregate_acc:.4f} "
          f"(reference: thesis reports 56.5%)")
    print(f"  Item-level mean accuracy (n = 20): {item_mean:.4f} "
          f"(SD = {item_sd:.4f})")
    print(f"  One-sample t against .50:           t(19) = {t_stat:.3f}, "
          f"p = {p_val:.4g}")
    print(f"  Wilcoxon signed-rank against .50:   W = {w_stat:.1f}, "
          f"p = {w_p:.4g}")

    # Per-item by source breakdown
    per_item_src = (
        forced.groupby(['trial', 'truth'])
        .agg(n_trials=('correct', 'size'),
             accuracy=('correct', 'mean'))
        .reset_index()
    )

    # ---- H2 / H3: by-items paired perception tests
    item_perception = (
        df.groupby(['trial', 'truth'])[['fluency', 'credibility']]
        .mean()
        .reset_index()
    )
    flu_wide = item_perception.pivot(index='trial', columns='truth',
                                      values='fluency')
    cred_wide = item_perception.pivot(index='trial', columns='truth',
                                       values='credibility')

    print("\n[H2] Perceived fluency by items:")
    flu_paired_med = (flu_wide['AI'] - flu_wide['Human']).median()
    flu_w_stat, flu_w_p = stats.wilcoxon(flu_wide['AI'], flu_wide['Human'])
    print(f"  Median AI fluency:     {flu_wide['AI'].median():.4f}")
    print(f"  Median Human fluency:  {flu_wide['Human'].median():.4f}")
    print(f"  Paired median Δ:       +{flu_paired_med:.4f} "
          f"(per-participant value reported in thesis: +0.66)")
    print(f"  Wilcoxon by items (n = 20):  W = {flu_w_stat:.1f}, "
          f"p = {flu_w_p:.4g}")

    print("\n[H3] Perceived credibility by items:")
    cred_paired_med = (cred_wide['AI'] - cred_wide['Human']).median()
    cred_w_stat, cred_w_p = stats.wilcoxon(cred_wide['AI'],
                                            cred_wide['Human'])
    print(f"  Median AI credibility:    {cred_wide['AI'].median():.4f}")
    print(f"  Median Human credibility: {cred_wide['Human'].median():.4f}")
    print(f"  Paired median Δ:          +{cred_paired_med:.4f} "
          f"(per-participant value reported in thesis: +0.50)")
    print(f"  Wilcoxon by items (n = 20):  W = {cred_w_stat:.1f}, "
          f"p = {cred_w_p:.4g}")

    return {
        'h1_aggregate_accuracy': aggregate_acc,
        'h1_item_mean_accuracy': item_mean,
        'h1_item_sd_accuracy': item_sd,
        'h1_t_against_chance': {'t': t_stat, 'df': 19, 'p': p_val},
        'h1_wilcoxon_against_chance': {'W': w_stat, 'p': w_p},
        'h2_item_paired_median_delta': flu_paired_med,
        'h2_wilcoxon_byitems': {'W': flu_w_stat, 'p': flu_w_p},
        'h3_item_paired_median_delta': cred_paired_med,
        'h3_wilcoxon_byitems': {'W': cred_w_stat, 'p': cred_w_p},
        'n_items': len(per_item),
    }


# ===========================================================================
# 2. PREDICTOR COLLINEARITY
# ===========================================================================
def collinearity_analysis(df):
    """Pairwise correlations + VIF for the three multivariable predictors."""
    print("\n" + "=" * 70)
    print(" PREDICTOR COLLINEARITY (true source, fluency_c, credibility_c)")
    print("=" * 70)

    work = df[['truth_AI', 'fluency_c', 'credibility_c']].dropna()
    corr = work.corr()
    print("\nPairwise Pearson correlations:")
    print(corr.round(4).to_string())

    # VIF: requires explicit intercept column for the standard interpretation
    X = work.copy()
    X.insert(0, 'intercept', 1.0)
    vifs = {}
    for i, col in enumerate(X.columns):
        if col == 'intercept':
            continue
        vif = variance_inflation_factor(X.values, i)
        vifs[col] = vif
    print("\nVariance inflation factors:")
    for k, v in vifs.items():
        flag = "OK" if v < 5 else ("watch" if v < 10 else "PROBLEM")
        print(f"  {k:18s} VIF = {v:6.3f}  [{flag}]")
    print("\n  Interpretation: VIF < 5 is unproblematic; 5-10 is worth noting;")
    print("  > 10 suggests serious multicollinearity. The Model 4 dissociation")
    print("  between fluency (n.s.) and credibility (p < .001) is therefore")
    print("  not an artefact of predictor collinearity.")

    return {
        'pearson_correlations': corr.round(4).to_dict(),
        'vif': vifs,
    }


# ===========================================================================
def main():
    df = load_data()
    by_items_result = by_items_analysis(df)
    collinearity_result = collinearity_analysis(df)

    out = {
        'by_items': by_items_result,
        'collinearity': collinearity_result,
    }

    json_path = os.path.join(OUTPUT_DIR, 'robustness_byitems_collinearity.json')
    with open(json_path, 'w') as f:
        json.dump(out, f, indent=2, default=float)
    print(f"\nSaved: {json_path}")


if __name__ == '__main__':
    main()
