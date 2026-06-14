"""
01_extract_and_analyse.py
=========================

Reads the Qualtrics CSV export of the thesis experiment, applies the
pre-registered quality filter, and runs every statistical test reported in
the Results section:

    H1.  Detection accuracy vs. chance      — exact binomial test
    H2.  Perceived fluency: AI vs. Human    — paired Wilcoxon signed-rank
    H3.  Perceived credibility: AI vs. Human — paired Wilcoxon signed-rank
    H4.  Fluency → source attribution        — fixed-effects ordinal regression
    H5.  Credibility → source attribution    — fixed-effects ordinal regression

It also writes a long-format trial-level dataset (`thesis_trial_data.csv`)
that is consumed by 02_generate_figures.py, 03_generate_tables.py, and the
R script mixed_effects_and_robustness.R.

Usage
-----
    python3 01_extract_and_analyse.py [--csv path/to/qualtrics_export.csv]

If --csv is omitted, the script looks for a Qualtrics export in the parent
project directory whose filename starts with "Reading Political Statements".

Author
------
Kerem Peker (ANR 2106332), Tilburg University CSAI BSc, 2026.
"""
import argparse
import csv
import glob
import json
import math
import os
import statistics as st
import sys

import pandas as pd
from scipy.stats import binomtest, norm, wilcoxon
from statsmodels.miscmodels.ordinal_model import OrderedModel


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
ATTR_MAP = {
    "Definitely AI-Generated":   1,
    "Probably AI-Generated":     2,
    "Not Sure":                  3,
    "Probably Human-Written":    4,
    "Definitely Human-Written":  5,
}

DURATION_MIN_SEC = 180     # exclude < 3 min (speedrunners)
DURATION_MAX_SEC = 3600    # exclude > 60 min (idle window)
N_TRIALS = 20              # per participant
N_FLUENCY_ITEMS = 5        # Graf et al. (2018) semantic differential
N_CREDIBILITY_ITEMS = 3    # Appelman & Sundar (2016)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def truth_label(set_assignment: str, trial: int) -> str:
    """Return 'AI' or 'Human' for a given Set + trial number.

    Counterbalancing: in Set A, odd-numbered trials are AI; in Set B, even
    are AI. The mapping is fixed by the experimental design.
    """
    if set_assignment == "A":
        return "AI" if trial % 2 == 1 else "Human"
    return "Human" if trial % 2 == 1 else "AI"


def find_default_csv() -> str:
    """Locate the most recent Qualtrics export in the parent directory."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = sorted(
        glob.glob(os.path.join(here, "..", "..", "Reading Political Statements*.csv"))
        + glob.glob(os.path.join(here, "..", "Reading Political Statements*.csv"))
    )
    if not candidates:
        sys.exit(
            "ERROR: No Qualtrics export found. Pass one with --csv path/to/file.csv"
        )
    return candidates[-1]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    p.add_argument("--csv", help="Path to Qualtrics export CSV")
    p.add_argument(
        "--out-dir",
        default=os.path.dirname(os.path.abspath(__file__)),
        help="Where to write thesis_trial_data.csv and _analysis_summary.json",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
def load_clean_rows(csv_path: str):
    """Return (header, idx, clean_rows) — Qualtrics drops 2 metadata rows
    before the actual data starts at row index 3."""
    with open(csv_path) as f:
        rows = list(csv.reader(f))
    header = rows[0]
    idx = {h: i for i, h in enumerate(header)}
    clean = [
        r for r in rows[3:]
        if r[idx["Finished"]].lower() == "true"
        and r[idx["Duration (in seconds)"]].isdigit()
        and DURATION_MIN_SEC <= int(r[idx["Duration (in seconds)"]]) <= DURATION_MAX_SEC
    ]
    return header, idx, clean


def build_trial_records(clean_rows, idx):
    """Reshape Qualtrics wide-format rows to long-format trial records and
    a per-participant aggregate dict."""
    parts = {}            # rid -> per-participant aggregates
    records = []          # one row per (participant, trial)

    for row in clean_rows:
        rid = row[idx["ResponseId"]]
        set_assignment = row[idx["SetAssignment"]]
        parts.setdefault(
            rid,
            {
                "set": set_assignment,
                "AI":    {"flu": [], "cred": [], "attr": [], "corr": [], "p_ai": []},
                "Human": {"flu": [], "cred": [], "attr": [], "corr": [], "p_ai": []},
            },
        )

        for t in range(1, N_TRIALS + 1):
            attr_raw = row[idx[f"Q{t}.1"]]
            fluency_items = [
                int(row[idx[f"Q{t}.2_{s}"]])
                for s in range(1, N_FLUENCY_ITEMS + 1)
                if row[idx[f"Q{t}.2_{s}"]].isdigit()
            ]
            credibility_items = [
                int(row[idx[f"Q{t}.3_{s}"]])
                for s in range(1, N_CREDIBILITY_ITEMS + 1)
                if row[idx[f"Q{t}.3_{s}"]].isdigit()
            ]

            # Skip incomplete trials
            if attr_raw not in ATTR_MAP or len(fluency_items) < 3 or len(credibility_items) < 2:
                continue

            attr = ATTR_MAP[attr_raw]
            truth = truth_label(set_assignment, t)
            fluency = st.mean(fluency_items)
            credibility = st.mean(credibility_items)
            p_ai_subjective = (5 - attr) / 4   # 1 -> 1.0 (AI), 5 -> 0.0 (Human)
            y = 1 if truth == "AI" else 0
            brier = (p_ai_subjective - y) ** 2

            parts[rid][truth]["flu"].append(fluency)
            parts[rid][truth]["cred"].append(credibility)
            parts[rid][truth]["attr"].append(attr)
            parts[rid][truth]["p_ai"].append(p_ai_subjective)
            if attr != 3:                       # Likert-3 excluded from forced-choice
                correct = (attr <= 2 and truth == "AI") or (attr >= 4 and truth == "Human")
                parts[rid][truth]["corr"].append(int(correct))

            records.append({
                "rid": rid, "set": set_assignment, "trial": t,
                "truth": truth, "truth_AI": y, "attr": attr,
                "fluency": fluency, "credibility": credibility,
                "p_ai_subj": p_ai_subjective, "brier": brier,
            })

    return parts, records


def report_demographics(clean_rows, idx):
    ages   = [int(r[idx["QID109"]]) for r in clean_rows if r[idx["QID109"]].isdigit()]
    eng    = [int(r[idx["QID112"]]) for r in clean_rows if r[idx["QID112"]].isdigit()]
    aifam  = [int(r[idx["QID113"]]) for r in clean_rows if r[idx["QID113"]].isdigit()]
    durs   = [int(r[idx["Duration (in seconds)"]]) for r in clean_rows]
    print(f"Age:             M = {st.mean(ages):.1f}, SD = {st.stdev(ages):.1f}, "
          f"range [{min(ages)}, {max(ages)}], n = {len(ages)}")
    print(f"English (1-7):   M = {st.mean(eng):.2f}, SD = {st.stdev(eng):.2f}")
    print(f"AI familiarity:  M = {st.mean(aifam):.2f}, SD = {st.stdev(aifam):.2f}")
    print(f"Duration:        median = {st.median(durs)/60:.1f} min, "
          f"M = {st.mean(durs)/60:.1f} min")


def wilcoxon_with_effect(a: list, b: list, label: str) -> dict:
    """Paired Wilcoxon signed-rank test with effect size r = z / sqrt(N)
    (Rosenthal, 1991)."""
    w = wilcoxon(a, b)
    z = norm.ppf(1 - w.pvalue / 2) if w.pvalue > 0 else 10
    r = z / math.sqrt(len(a))
    med_diff = st.median([x - y for x, y in zip(a, b)])
    print(f"  Median AI = {st.median(a):.3f}; Median Human = {st.median(b):.3f}")
    print(f"  Mean AI = {st.mean(a):.3f} (SD = {st.stdev(a):.3f}); "
          f"Human = {st.mean(b):.3f} (SD = {st.stdev(b):.3f})")
    print(f"  Wilcoxon V = {w.statistic:.1f}, p = {w.pvalue:.4g}, "
          f"r = z/sqrt(N) = {r:.3f}, median diff = +{med_diff:.3f}")
    return {"V": float(w.statistic), "p": float(w.pvalue), "r": r, "median_diff": med_diff}


def run_ordinal_models(records: list) -> dict:
    """Four nested proportional-odds ordinal logistic regressions."""
    df = pd.DataFrame(records)
    df["fluency_c"] = df["fluency"] - df["fluency"].mean()
    df["credibility_c"] = df["credibility"] - df["credibility"].mean()

    def _fit(predictors, label):
        m = OrderedModel(df["attr"], df[predictors], distr="logit").fit(
            method="bfgs", disp=False)
        out = {}
        for p in predictors:
            out[p] = {
                "beta": float(m.params[p]),
                "se":   float(m.bse[p]),
                "z":    float(m.tvalues[p]),
                "p":    float(m.pvalues[p]),
                "OR":   math.exp(m.params[p]),
            }
        print(f"\n  {label}")
        for p, v in out.items():
            print(f"    {p}: beta = {v['beta']:+.3f}, SE = {v['se']:.3f}, "
                  f"z = {v['z']:+.2f}, p = {v['p']:.4g}, OR = {v['OR']:.3f}")
        return out

    return {
        "M1_truth_only":           _fit(["truth_AI"],                                 "Model 1: truth only"),
        "M2_fluency_only_H4":      _fit(["fluency_c"],                                "Model 2 (H4): fluency only"),
        "M3_credibility_only_H5":  _fit(["credibility_c"],                            "Model 3 (H5): credibility only"),
        "M4_full":                 _fit(["truth_AI", "fluency_c", "credibility_c"],   "Model 4 (full multivariable)"),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = parse_args()
    csv_path = args.csv or find_default_csv()
    print(f"Reading: {csv_path}\n")

    header, idx, clean_rows = load_clean_rows(csv_path)
    parts, records = build_trial_records(clean_rows, idx)

    # ---- sample ----
    print("===== SAMPLE =====")
    print(f"N participants (after duration filter {DURATION_MIN_SEC}-{DURATION_MAX_SEC}s): "
          f"{len(parts)}")
    set_a = sum(1 for p in parts.values() if p["set"] == "A")
    print(f"Set A / Set B: {set_a} / {len(parts) - set_a}")
    print(f"Trial-level observations: {len(records)}")
    report_demographics(clean_rows, idx)

    # ---- H1: detection accuracy ----
    print("\n===== H1: DETECTION ACCURACY (binomial vs chance) =====")
    forced = [r for r in records if r["attr"] != 3]
    correct_count = sum(
        1 for r in forced
        if (r["attr"] <= 2 and r["truth_AI"] == 1)
        or (r["attr"] >= 4 and r["truth_AI"] == 0)
    )
    n_forced = len(forced)
    b_test = binomtest(correct_count, n_forced, p=0.5)
    ci = b_test.proportion_ci()
    print(f"  {correct_count}/{n_forced} = {correct_count / n_forced:.3f}")
    print(f"  Binomial p = {b_test.pvalue:.4g}, 95% CI [{ci[0]:.3f}, {ci[1]:.3f}]")

    acc_per_pp = []
    for p in parts.values():
        all_corr = p["AI"]["corr"] + p["Human"]["corr"]
        if all_corr:
            acc_per_pp.append(sum(all_corr) / len(all_corr))
    print(f"  Per-participant accuracy: M = {st.mean(acc_per_pp):.3f}, "
          f"SD = {st.stdev(acc_per_pp):.3f}, N = {len(acc_per_pp)}")
    # Paired by participant: require both AI-forced and Human-forced trials per pp
    paired = [(p["AI"]["corr"], p["Human"]["corr"]) for p in parts.values()
              if p["AI"]["corr"] and p["Human"]["corr"]]
    sens = [sum(ai) / len(ai) for ai, _ in paired]
    spec = [sum(hu) / len(hu) for _, hu in paired]
    print(f"  Sensitivity (AI correct):    M = {st.mean(sens):.3f}")
    print(f"  Specificity (Human correct): M = {st.mean(spec):.3f}")
    sens_spec_test = wilcoxon(spec, sens)
    print(f"  Paired Wilcoxon (specificity > sensitivity): "
          f"V = {sens_spec_test.statistic:.1f}, p = {sens_spec_test.pvalue:.4g}")

    # ---- H2 & H3 ----
    ai_flu  = [st.mean(p["AI"]["flu"])    for p in parts.values()]
    hu_flu  = [st.mean(p["Human"]["flu"]) for p in parts.values()]
    ai_cred = [st.mean(p["AI"]["cred"])   for p in parts.values()]
    hu_cred = [st.mean(p["Human"]["cred"])for p in parts.values()]
    print("\n===== H2: PERCEIVED FLUENCY (Wilcoxon paired) =====")
    h2 = wilcoxon_with_effect(ai_flu, hu_flu, "fluency")
    print("\n===== H3: PERCEIVED CREDIBILITY (Wilcoxon paired) =====")
    h3 = wilcoxon_with_effect(ai_cred, hu_cred, "credibility")

    # ---- H4 & H5: ordinal regression ----
    print("\n===== H4 & H5: ORDINAL LOGISTIC REGRESSION =====")
    ordinal_results = run_ordinal_models(records)

    # ---- save ----
    os.makedirs(args.out_dir, exist_ok=True)
    csv_out = os.path.join(args.out_dir, "thesis_trial_data.csv")
    pd.DataFrame(records).to_csv(csv_out, index=False)

    summary = {
        "n_participants": len(parts),
        "n_trials": len(records),
        "set_A": set_a, "set_B": len(parts) - set_a,
        "H1": {"correct": correct_count, "total_forced": n_forced,
               "binomial_p": float(b_test.pvalue),
               "ci_low": float(ci[0]), "ci_high": float(ci[1])},
        "H2_fluency": h2,
        "H3_credibility": h3,
        "ordinal_models": ordinal_results,
    }
    json_out = os.path.join(args.out_dir, "_analysis_summary.json")
    with open(json_out, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\nSaved: {csv_out}")
    print(f"Saved: {json_out}")


if __name__ == "__main__":
    main()
