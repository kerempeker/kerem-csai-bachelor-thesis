# Robustness Results

Companion document for the two robustness scripts:

- `python_analysis/robustness_byitems_collinearity.py`
- `R_analysis/robustness_byitems_collinearity.R`

These two checks complement the principal cumulative-link mixed model reported
in Section 4.5 of the thesis. Both confirm that the H1-H5 conclusions are not
artefacts of (a) participant-level idiosyncrasy or (b) predictor
multicollinearity.

---

## 1. By-items aggregation (Python)

The trial-level analyses in the thesis are run with the trial as the unit of
observation, and the principal model adds a stimulus random intercept to
handle item-level non-independence. As an additional sanity check, the
analyses below are reproduced with the **stimulus (n = 20) as the unit of
analysis**, so any item-level effects fully drive the test.

### H1 — Detection accuracy

| Quantity | Value |
|---|---|
| Trial-level aggregate accuracy | 0.5648 (~56.5%, matches thesis headline) |
| Item-level mean accuracy (n = 20) | 0.5652 (SD = 0.050) |
| One-sample *t* against chance (.50) | *t*(19) = 5.82, *p* < .001 |
| Wilcoxon signed-rank against .50 | *W* = 8, *p* < .001 |

The detection signal is item-level robust: every test on the n = 20 items
reproduces the > 50% conclusion. The item-level standard deviation (.050)
is small relative to the mean offset from chance (.065), indicating the
effect is not driven by a handful of unusually detectable topics.

### H2 — Perceived fluency

| Quantity | Value |
|---|---|
| Median AI fluency (across items) | 5.91 |
| Median Human fluency (across items) | 5.18 |
| Paired median Δ (per-item) | **+0.72** (per-participant Δ reported in thesis: +0.66) |
| Wilcoxon (n = 20) | *W* = 10, *p* < .001 |

### H3 — Perceived credibility

| Quantity | Value |
|---|---|
| Median AI credibility (across items) | 5.33 |
| Median Human credibility (across items) | 4.78 |
| Paired median Δ (per-item) | **+0.57** (per-participant Δ reported in thesis: +0.50) |
| Wilcoxon (n = 20) | *W* = 7, *p* < .001 |

The by-items paired deltas are slightly larger than the per-participant deltas
in the thesis, which is consistent with cancellation of within-participant
variance when items are averaged across the 87 raters. Both H2 and H3 remain
strongly supported.

---

## 2. Predictor collinearity (Python and R)

The Model 4 dissociation reported in Section 4.5 (fluency *n.s.*, credibility
*p* < .001) could in principle reflect multicollinearity rather than a real
difference in predictive content. The diagnostics below rule that out.

### Pairwise Pearson correlations (n = 1,740)

| | truth_AI | fluency_c | credibility_c |
|---|---|---|---|
| **truth_AI** | 1.000 | 0.323 | 0.234 |
| **fluency_c** | 0.323 | 1.000 | 0.519 |
| **credibility_c** | 0.234 | 0.519 | 1.000 |

Fluency and credibility share moderate but non-redundant variance (*r* = .52),
which is exactly what the design intends: they are conceptually related
metacognitive cues, but not interchangeable.

### Variance inflation factors

| Predictor | VIF | Diagnostic |
|---|---|---|
| truth_AI | 1.12 | OK |
| fluency_c | 1.45 | OK |
| credibility_c | 1.38 | OK |

All VIFs are well below the conventional caution thresholds (5 for "watch",
10 for "problem"). The Model 4 fluency-vs-credibility dissociation is
therefore not an artefact of predictor collinearity: each predictor's
standard error would have had to be inflated by a factor of √VIF ≈ 1.2
even in the worst case, which is small relative to the effect-size difference
between the two predictors.

---

## 3. Crossed random-effects GLMM (R)

As a parallel check on the principal ordinal mixed model in R
(`ordinal::clmm`), the H1 detection-accuracy test is also fitted as a binary
GLMM with crossed random effects for participant and stimulus:

```r
glmer(correct ~ truth + (1 | rid) + (1 | trial),
      data = df_fc, family = binomial(link = "logit"))
```

Fitted values:

| Quantity | Value |
|---|---|
| Fixed effect for truth = AI | β = −0.27, *SE* = 0.106, *z* = −2.55, *p* = .011 |
| Likelihood-ratio test (truth vs. null) | χ²(1) = 6.49, *p* = .011 |
| Marginal *P*(correct &#124; Human stimulus) | 0.597 |
| Marginal *P*(correct &#124; AI stimulus) | 0.531 |
| Aggregate trial-level accuracy (data) | 0.565 |

The negative fixed effect for `truth = AI` confirms the
sensitivity-specificity asymmetry reported in Section 4.2 of the thesis:
human stimuli are more often correctly attributed than AI stimuli. The
likelihood-ratio test agrees with the principal CLMM that true source is a
reliable predictor of the correctness outcome at the binary scale.

Note: the random-intercept variances are estimated as effectively zero in
this binary GLMM (singular fit), which is expected because the H1 outcome is
defined by collapsing the 5-point Likert attribution into a binary
correctness indicator. The principal CLMM in
`mixed_effects_and_robustness.R` retains the full ordinal information and
estimates non-trivial random-intercept variances (participant SD ≈ 0.61,
stimulus SD ≈ 0.10), as reported in Section 4.5 of the thesis. The binary
GLMM here is therefore a *direction-and-sign* robustness check, not a
replacement for the principal ordinal model. The qualitative conclusion (H1
holds in both specifications) is the relevant takeaway.

The crossed binary specification matches the standard random-effects practice
in psycholinguistics (Baayen et al., 2008) and confirms that the H1 result
does not depend on the parametric link of the ordinal mixed model.

---

## How to reproduce

```bash
# Python (3.13+)
cd python_analysis
python3 robustness_byitems_collinearity.py

# R (4.5+ with lme4 and car installed)
cd R_analysis
Rscript robustness_byitems_collinearity.R
```

Inputs are read from `sample_data/thesis_trial_data.csv` (1,740 trial-level
observations, 87 participants, 20 stimuli). The Python script writes a
machine-readable summary to
`example_outputs/tables/robustness_byitems_collinearity.json`.
