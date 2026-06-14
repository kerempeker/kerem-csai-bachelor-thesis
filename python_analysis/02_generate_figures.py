#!/usr/bin/env python3
"""
Generates all 9 thesis figures from the trial-level CSV.

Polished APA-style figures: consistent serif typography, restrained colour
palette (warm orange for AI, deep blue for Human), restrained gridlines,
generous padding so labels and titles do not collide.

Usage:
    python3 generate_figures.py

Inputs:
    ../thesis_trial_data.csv     (1,740 trial-level observations)

Outputs:
    ../figures/fig{1..9}_*.png

Dependencies:
    Python 3.13, matplotlib 3.8+, pandas 2.2+, numpy 2.0+, statsmodels 0.14+

Author: Kerem Peker (ANR 2106332), Tilburg University CSAI BSc, 2026.
"""
import os
import sys
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from statsmodels.miscmodels.ordinal_model import OrderedModel


# ---------------------------------------------------------------------------
# Paths and styling
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)

# Try the zip-submission layout first (sample_data/, example_outputs/figures/),
# then fall back to the repo layout (thesis_trial_data.csv at the project root,
# figures/ at the project root).
def _resolve_paths():
    candidates_in = [
        os.path.join(PROJECT_ROOT, 'sample_data', 'thesis_trial_data.csv'),
        os.path.join(PROJECT_ROOT, 'thesis_trial_data.csv'),
    ]
    csv_path = next((p for p in candidates_in if os.path.exists(p)), candidates_in[0])
    if os.path.basename(os.path.dirname(csv_path)) == 'sample_data':
        out_dir = os.path.join(PROJECT_ROOT, 'example_outputs', 'figures')
    else:
        out_dir = os.path.join(PROJECT_ROOT, 'figures')
    return csv_path, out_dir


INPUT_CSV, OUTPUT_DIR = _resolve_paths()
os.makedirs(OUTPUT_DIR, exist_ok=True)

plt.rcParams.update({
    'font.family': 'DejaVu Serif',
    'font.size': 11,
    'axes.labelsize': 11.5,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.titlelocation': 'left',
    'axes.titlepad': 14,
    'axes.labelpad': 8,
    'axes.spines.top': False,
    'axes.spines.right': False,
    'axes.linewidth': 1.0,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'xtick.major.pad': 5,
    'ytick.major.pad': 5,
    'legend.fontsize': 10,
    'legend.frameon': False,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.35,
    'savefig.facecolor': 'white',
})

AI_COLOR = '#d97a26'   # warm orange — AI condition
HU_COLOR = '#1f6fb4'   # deep blue   — human condition
GRAY     = '#888888'
DARK     = '#2b2b2b'


# ---------------------------------------------------------------------------
def load_data() -> pd.DataFrame:
    if not os.path.exists(INPUT_CSV):
        sys.exit(f"ERROR: Cannot find {INPUT_CSV}. Run _final_analysis.py first.")
    df = pd.read_csv(INPUT_CSV)
    print(f"Loaded {len(df)} trials from {df.rid.nunique()} participants")
    return df


# ---------------------------------------------------------------------------
# Figure 1 — Sample funnel (polished)
# ---------------------------------------------------------------------------
def fig6_sample_funnel() -> None:
    fig, ax = plt.subplots(figsize=(9, 5.5))
    stages = [
        ("Total responses started",                    "n = 131",         GRAY,    None),
        ("Completed (Finished = True)",                "n = 93",          GRAY,    "38 abandoned the survey"),
        ("Passed quality filter\n(3–60 min duration)", "n = 87",          HU_COLOR, "1 speedrun (< 3 min);\n5 idle window (> 60 min)"),
        ("Trial-level observations",                   "20 × 87 = 1,740", AI_COLOR, None),
    ]
    n_stages = len(stages)
    box_h = 0.9
    cx = 0.34
    sizes = [1.0, 0.78, 0.74, 1.0]
    for i, ((title, n_lbl, color, note), size) in enumerate(zip(stages, sizes)):
        y = n_stages - 1 - i
        w = 0.30 + 0.42 * size
        box = mpatches.FancyBboxPatch(
            (cx - w / 2, y - box_h / 2), w, box_h,
            boxstyle="round,pad=0.04,rounding_size=0.08",
            facecolor=color, alpha=0.85, edgecolor=DARK, linewidth=1.5)
        ax.add_patch(box)
        ax.text(cx, y + 0.10, title, ha='center', va='center',
                fontsize=10.5, color='white', fontweight='bold')
        ax.text(cx, y - 0.22, n_lbl, ha='center', va='center',
                fontsize=12, color='white', fontweight='bold')
        if i < n_stages - 1:
            ax.annotate('',
                        xy=(cx, y - box_h / 2 - 0.18),
                        xytext=(cx, y - box_h / 2 - 0.02),
                        arrowprops=dict(arrowstyle='->', color=DARK, lw=1.8,
                                        mutation_scale=18))
            if note:
                ax.text(cx + w / 2 + 0.08, y - box_h / 2 - 0.10,
                        f'→ {note}', fontsize=10, color='#b03030',
                        style='italic', va='center', ha='left')
    ax.set_xlim(0, 1.0); ax.set_ylim(-0.7, n_stages - 0.3); ax.axis('off')
    ax.set_title('Sample funnel from data collection to analytic sample')
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig6_sample_funnel.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 2 — Per-participant accuracy distribution
# ---------------------------------------------------------------------------
def fig5_accuracy_distribution(df: pd.DataFrame) -> None:
    forced = df[df['attr'] != 3].copy()
    forced['correct'] = ((forced['attr'] <= 2) & (forced['truth_AI'] == 1)) | \
                        ((forced['attr'] >= 4) & (forced['truth_AI'] == 0))
    acc = forced.groupby('rid')['correct'].mean()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.hist(acc, bins=18, color=HU_COLOR, alpha=0.75,
            edgecolor='white', linewidth=0.8)
    ax.axvline(0.5, color='#c0392b', linestyle='--', linewidth=1.8,
               label='Chance (50%)', zorder=5)
    ax.axvline(acc.mean(), color=DARK, linestyle='-', linewidth=2.0,
               label=f'Sample mean ({acc.mean():.3f})', zorder=5)
    ax.set_xlabel('Per-participant detection accuracy')
    ax.set_ylabel('Number of participants')
    ax.set_title(f'Distribution of per-participant detection accuracy (N = {df.rid.nunique()})')
    ax.set_xlim(0, 1)
    ax.legend(loc='upper right')
    ax.grid(True, axis='y', alpha=0.25)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig5_accuracy_distribution.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 3 — Confusion matrix
# ---------------------------------------------------------------------------
def fig3_confusion_matrix(df: pd.DataFrame) -> None:
    def attr_cat(a):
        return 'Judged AI' if a <= 2 else ('Uncertain' if a == 3 else 'Judged Human')
    dfa = df.assign(judged=df['attr'].apply(attr_cat))
    cm = pd.crosstab(dfa['truth'], dfa['judged'])[['Judged AI', 'Uncertain', 'Judged Human']]
    cm_prop = cm.div(cm.sum(axis=1), axis=0)

    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    im = ax.imshow(cm_prop.values, cmap='Blues', vmin=0, vmax=0.6, aspect='auto')
    ax.set_xticks(range(3))
    ax.set_xticklabels(cm_prop.columns)
    ax.set_yticks(range(2))
    ax.set_yticklabels(['True AI', 'True Human'])
    ax.set_xlabel('Participant judgment')
    ax.set_ylabel('True source')
    ax.set_title('Source-attribution confusion matrix (row-normalised)')
    for i in range(2):
        for j in range(3):
            prop = cm_prop.values[i, j]
            cnt = cm.values[i, j]
            color = 'white' if prop > 0.35 else DARK
            ax.text(j, i, f"{prop:.2f}\n(n = {cnt})",
                    ha='center', va='center',
                    color=color, fontsize=11.5, fontweight='bold')
    cbar = plt.colorbar(im, ax=ax, shrink=0.85, pad=0.04)
    cbar.set_label('Row proportion', size=10.5)
    cbar.ax.tick_params(labelsize=9.5)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig3_confusion_matrix.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 4 — Paired perception box plots
# ---------------------------------------------------------------------------
def fig1_perception_boxplots(df: pd.DataFrame) -> None:
    agg = df.groupby(['rid', 'truth'])[['fluency', 'credibility']].mean().reset_index()
    pivot_flu = agg.pivot(index='rid', columns='truth', values='fluency')
    pivot_cred = agg.pivot(index='rid', columns='truth', values='credibility')

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 5))
    for ax, pivot, sub_title, ylab in zip(
            axes,
            [pivot_flu, pivot_cred],
            ['(a) Perceived fluency', '(b) Perceived credibility'],
            ['Fluency (1–7)', 'Credibility (1–7)']):
        for _, row in pivot.iterrows():
            ax.plot([0, 1], [row['AI'], row['Human']],
                    color=GRAY, alpha=0.18, linewidth=0.7)
        bp = ax.boxplot([pivot['AI'].dropna(), pivot['Human'].dropna()],
                        positions=[0, 1], widths=0.42, patch_artist=True,
                        medianprops=dict(color=DARK, linewidth=2),
                        boxprops=dict(linewidth=1.3, edgecolor=DARK),
                        whiskerprops=dict(linewidth=1.3, color=DARK),
                        capprops=dict(linewidth=1.3, color=DARK),
                        flierprops=dict(marker='o', markersize=4,
                                        markerfacecolor=GRAY,
                                        markeredgecolor=DARK, alpha=0.5))
        bp['boxes'][0].set_facecolor(AI_COLOR); bp['boxes'][0].set_alpha(0.78)
        bp['boxes'][1].set_facecolor(HU_COLOR); bp['boxes'][1].set_alpha(0.78)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(['AI-generated', 'Human-authored'])
        ax.set_ylabel(ylab)
        ax.set_title(sub_title)
        ax.set_ylim(1, 7.4)
        ax.grid(True, axis='y', alpha=0.25)
        med_ai = pivot['AI'].median(); med_hu = pivot['Human'].median()
        ax.annotate(f'median Δ = +{med_ai - med_hu:.2f}',
                    xy=(0.5, 7.15), ha='center', fontsize=10, style='italic',
                    color=DARK)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig1_perception_boxplots.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 5 — Forest plot of ordinal regression coefficients
# ---------------------------------------------------------------------------
def fig4_forest_plot() -> None:
    results = [
        ('Model 1: Truth only',            'Truth = AI',  -0.487, 0.086, 0.62),
        ('Model 2 (H4): Fluency only',     'Fluency',     +0.057, 0.047, 1.06),
        ('Model 3 (H5): Credibility only', 'Credibility', +0.225, 0.043, 1.25),
        ('Model 4: Full multivariable',    'Truth = AI',  -0.602, 0.090, 0.55),
        ('Model 4: Full multivariable',    'Fluency',     -0.027, 0.057, 0.97),
        ('Model 4: Full multivariable',    'Credibility', +0.303, 0.051, 1.35),
    ]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ylabels = []
    for i, (model, pred, beta, se, OR) in enumerate(results):
        y = len(results) - i
        ci_lo, ci_hi = beta - 1.96 * se, beta + 1.96 * se
        color = AI_COLOR if pred == 'Truth = AI' else (HU_COLOR if pred == 'Credibility' else GRAY)
        ax.errorbar(beta, y, xerr=[[beta - ci_lo], [ci_hi - beta]],
                    fmt='o', color=color, ecolor=color, capsize=5,
                    markersize=9, linewidth=2.2, markeredgecolor=DARK,
                    markeredgewidth=0.8)
        ylabels.append(f"{model}\n[{pred}]")
        ax.annotate(f'OR = {OR:.2f}', xy=(ci_hi + 0.06, y),
                    va='center', fontsize=10, color=DARK)
    ax.axvline(0, color=DARK, linestyle='-', linewidth=1)
    ax.set_yticks(range(len(results), 0, -1))
    ax.set_yticklabels(ylabels, fontsize=9.5)
    ax.set_xlabel('Log-odds coefficient (β) ± 95% CI')
    ax.set_title('Ordinal logistic regression: predictors of source attribution')
    ax.set_xlim(-0.9, 0.95)
    ax.grid(True, axis='x', alpha=0.25)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig4_forest_plot.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 6 — Per-stimulus accuracy bar chart
# ---------------------------------------------------------------------------
def fig2_per_stimulus_accuracy(df: pd.DataFrame) -> None:
    forced = df[df['attr'] != 3].copy()
    forced['correct'] = ((forced['attr'] <= 2) & (forced['truth_AI'] == 1)) | \
                        ((forced['attr'] >= 4) & (forced['truth_AI'] == 0))
    per_stim = (forced.groupby(['trial', 'truth'])['correct']
                .mean().reset_index())
    per_stim_wide = per_stim.pivot(index='trial', columns='truth', values='correct')

    fig, ax = plt.subplots(figsize=(12, 4.8))
    x = np.arange(1, 21)
    w = 0.4
    ax.bar(x - w / 2, per_stim_wide['AI'], w,
           label='AI-generated text', color=AI_COLOR, alpha=0.88,
           edgecolor=DARK, linewidth=0.6)
    ax.bar(x + w / 2, per_stim_wide['Human'], w,
           label='Human-authored text', color=HU_COLOR, alpha=0.88,
           edgecolor=DARK, linewidth=0.6)
    ax.axhline(0.5, color='#c0392b', linestyle='--', linewidth=1.5,
               alpha=0.85, label='Chance (50%)', zorder=5)
    ax.set_xlabel('Stimulus topic')
    ax.set_ylabel('Detection accuracy')
    ax.set_title('Per-stimulus detection accuracy across 20 topics')
    ax.set_xticks(x)
    ax.set_xlim(0.4, 20.6)
    ax.set_ylim(0, 1)
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.25), ncol=3)
    ax.grid(True, axis='y', alpha=0.25)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig2_per_stimulus_accuracy.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 7 — Predicted probabilities by credibility (stacked area)
# ---------------------------------------------------------------------------
def fig7_predicted_probabilities(df: pd.DataFrame) -> None:
    dff = df.copy()
    dff['fluency_c'] = dff['fluency'] - dff['fluency'].mean()
    dff['credibility_c'] = dff['credibility'] - dff['credibility'].mean()
    m4 = OrderedModel(dff['attr'],
                      dff[['truth_AI', 'fluency_c', 'credibility_c']],
                      distr='logit').fit(method='bfgs', disp=False)
    cred_range = np.linspace(-2.5, 2.5, 200)
    X = pd.DataFrame({'truth_AI': 0.5, 'fluency_c': 0, 'credibility_c': cred_range})
    pred_probs = m4.model.predict(m4.params, exog=X)

    fig, ax = plt.subplots(figsize=(10, 5.2))
    labels = ['1: Definitely AI', '2: Probably AI', '3: Not sure',
              '4: Probably Human', '5: Definitely Human']
    colors = ['#c0392b', '#e87722', '#f4d03f', '#5dade2', '#1f6fb4']
    cum_low = np.zeros_like(cred_range)
    for cat in range(5):
        cum_high = pred_probs[:, :cat + 1].sum(axis=1)
        ax.fill_between(cred_range, cum_low, cum_high,
                        color=colors[cat], alpha=0.82, label=labels[cat],
                        edgecolor='white', linewidth=0.3)
        cum_low = cum_high
    ax.set_xlim(-2.5, 2.5); ax.set_ylim(0, 1)
    ax.set_xlabel('Perceived credibility (mean-centred)')
    ax.set_ylabel('Predicted probability')
    ax.set_title('Predicted attribution probabilities by perceived credibility (Model 4)')
    ax.legend(loc='center left', bbox_to_anchor=(1.02, 0.5),
              title='Attribution rating', title_fontsize=10)
    ax.grid(False)
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig7_predicted_probabilities.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 8 — Trial-structure schematic (within-subjects design)
# ---------------------------------------------------------------------------
def fig8_trial_structure() -> None:
    fig, ax = plt.subplots(figsize=(13, 5.2))

    stages = [
        ("Trial onset",          "(text appears)",                          GRAY),
        ("Read stimulus",        "(50–79-word\npolitical text)",            HU_COLOR),
        ("Source attribution",   "5-point ordinal\nJakesch et al. (2023)",  AI_COLOR),
        ("Perceived fluency",    "5-item semantic\ndifferential\nGraf et al. (2018)", AI_COLOR),
        ("Perceived credibility", "3-item Likert\nAppelman &\nSundar (2016)", AI_COLOR),
    ]

    n = len(stages)
    box_w = 2.45
    box_h = 2.6
    gap = 0.32
    y_center = 2.8
    x0 = 0.6

    for i, (title, sub, color) in enumerate(stages):
        x = x0 + i * (box_w + gap)
        box = mpatches.FancyBboxPatch(
            (x, y_center - box_h / 2), box_w, box_h,
            boxstyle="round,pad=0.04,rounding_size=0.10",
            facecolor=color, alpha=0.88, edgecolor=DARK, linewidth=1.4)
        ax.add_patch(box)
        ax.text(x + box_w / 2, y_center + 0.55, title,
                ha='center', va='center', fontsize=10.5,
                color='white', fontweight='bold')
        ax.text(x + box_w / 2, y_center - 0.55, sub,
                ha='center', va='center', fontsize=9.5,
                color='white', style='italic')
        if i < n - 1:
            ax.annotate(
                '', xy=(x + box_w + gap - 0.03, y_center),
                xytext=(x + box_w + 0.03, y_center),
                arrowprops=dict(arrowstyle='->', color=DARK, lw=1.8,
                                mutation_scale=20))

    total_w = n * box_w + (n - 1) * gap
    ax.annotate(
        '', xy=(x0 + total_w, 0.7),
        xytext=(x0, 0.7),
        arrowprops=dict(arrowstyle='<->', color=DARK, lw=1.4,
                        linestyle='dashed', mutation_scale=18))
    ax.text(x0 + total_w / 2, 0.30,
            '× 20 trials  (counterbalanced; random order within set)',
            ha='center', va='center', fontsize=10.5,
            color=DARK, style='italic')

    ax.set_xlim(-0.3, x0 + total_w + 1.0)
    ax.set_ylim(0, 5.2)
    ax.axis('off')
    ax.set_title('Structure of a single trial in the within-subjects design')
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig8_trial_structure.png'))
    plt.close()


# ---------------------------------------------------------------------------
# Figure 9 — Robustness of H1 to four codings of the Likert-3 "Not sure"
# ---------------------------------------------------------------------------
def fig9_likert3_robustness(df: pd.DataFrame) -> None:
    """Detection accuracy under four alternative codings of the Likert-3
    midpoint ("Not sure"), with Wilson 95 % CIs.

    Codings:
      (a) Forced-choice: drop all Likert-3 responses (1,459 trials remain).
      (b) Likert-3 coded as an "AI" judgment (incorrect for human stimuli).
      (c) Likert-3 coded as a "Human" judgment (incorrect for AI stimuli).
      (d) Likert-3 awarded half-credit (0.5 correct, 0.5 incorrect).
    """
    from statsmodels.stats.proportion import proportion_confint

    truth_ai = (df['truth_AI'] == 1)

    # (a) Forced-choice: exclude midpoint
    fc = df[df['attr'] != 3]
    fc_correct = ((fc['attr'] <= 2) & (fc['truth_AI'] == 1)) | \
                 ((fc['attr'] >= 4) & (fc['truth_AI'] == 0))
    n_a = len(fc); k_a = fc_correct.sum()

    # (b) Likert-3 coded as AI
    correct_b = ((df['attr'] <= 3) & truth_ai) | \
                ((df['attr'] >= 4) & ~truth_ai)
    n_b = len(df); k_b = correct_b.sum()

    # (c) Likert-3 coded as Human
    correct_c = ((df['attr'] <= 2) & truth_ai) | \
                ((df['attr'] >= 3) & ~truth_ai)
    n_c = len(df); k_c = correct_c.sum()

    # (d) Likert-3 = half credit (sum of weights / N)
    weights = np.where(
        df['attr'] == 3, 0.5,
        np.where(((df['attr'] <= 2) & truth_ai) | ((df['attr'] >= 4) & ~truth_ai), 1.0, 0.0))
    n_d = len(df); k_d = weights.sum()

    bars = [
        ('Forced-choice\n(Likert-3 excluded)', k_a, n_a, HU_COLOR),
        ('Likert-3 coded\nas "AI" judgment',   k_b, n_b, AI_COLOR),
        ('Likert-3 coded\nas "Human" judgment', k_c, n_c, AI_COLOR),
        ('Likert-3 awarded\nhalf-credit',       k_d, n_d, GRAY),
    ]

    fig, ax = plt.subplots(figsize=(10, 5.2))
    x = np.arange(len(bars))
    for i, (label, k, n, color) in enumerate(bars):
        p_hat = k / n
        # Wilson CI; round counts for binomial CI on the half-credit case
        ci_lo, ci_hi = proportion_confint(int(round(k)), n, alpha=0.05, method='wilson')
        ax.bar(i, p_hat, width=0.58, color=color, alpha=0.88,
               edgecolor=DARK, linewidth=0.8)
        ax.errorbar(i, p_hat, yerr=[[p_hat - ci_lo], [ci_hi - p_hat]],
                    fmt='none', ecolor=DARK, capsize=6, linewidth=1.6)
        k_disp = f'{k:.1f}' if isinstance(k, float) else f'{k}'
        ax.text(i, ci_hi + 0.012,
                f'{p_hat * 100:.1f}%\n({k_disp}/{n})',
                ha='center', va='bottom', fontsize=10, color=DARK,
                fontweight='bold')

    ax.axhline(0.5, color='#c0392b', linestyle='--', linewidth=1.6,
               label='Chance (50%)', zorder=5)
    ax.set_xticks(x)
    ax.set_xticklabels([b[0] for b in bars], fontsize=10)
    ax.set_ylabel('Detection accuracy')
    ax.set_ylim(0.45, 0.65)
    ax.set_yticks(np.arange(0.45, 0.66, 0.025))
    ax.grid(True, axis='y', alpha=0.25)
    ax.legend(loc='upper right')
    ax.set_title('Robustness of the H1 detection-accuracy result to four codings of the Likert-3 "Not sure" response')
    plt.savefig(os.path.join(OUTPUT_DIR, 'fig9_likert3_robustness.png'))
    plt.close()


# ---------------------------------------------------------------------------
def main() -> None:
    df = load_data()
    print("Generating figures...")
    fig6_sample_funnel();             print("  ✓ fig6_sample_funnel.png      (Figure 1 in thesis)")
    fig5_accuracy_distribution(df);   print("  ✓ fig5_accuracy_distribution.png (Figure 2)")
    fig3_confusion_matrix(df);        print("  ✓ fig3_confusion_matrix.png   (Figure 3)")
    fig1_perception_boxplots(df);     print("  ✓ fig1_perception_boxplots.png (Figure 4)")
    fig4_forest_plot();               print("  ✓ fig4_forest_plot.png        (Figure 5)")
    fig2_per_stimulus_accuracy(df);   print("  ✓ fig2_per_stimulus_accuracy.png (Figure 6)")
    fig7_predicted_probabilities(df); print("  ✓ fig7_predicted_probabilities.png (Figure 7)")
    fig8_trial_structure();           print("  ✓ fig8_trial_structure.png    (Figure 8)")
    fig9_likert3_robustness(df);      print("  ✓ fig9_likert3_robustness.png (Figure 9)")
    print(f"\nAll figures saved to: {OUTPUT_DIR}")


if __name__ == '__main__':
    main()
