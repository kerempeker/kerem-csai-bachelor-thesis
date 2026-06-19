# ============================================================
# Robustness check: lme4 crossed random-effects model
# ============================================================
# Complements the principal cumulative-link mixed model (ordinal::clmm) in
# mixed_effects_and_robustness.R by refitting the same data with a binary
# correctness outcome and a crossed random-effects structure in lme4:
#
#   correct ~ truth + (1 | rid) + (1 | trial)
#
# This serves as a robustness check against the parametric link of the
# principal ordinal model, isolating the H1 detection-accuracy result under a
# binary GLMM specification that is widely used in psycholinguistics for
# crossed by-subject and by-item random effects (Baayen et al., 2008).
#
# Also reports the predictor-collinearity diagnostics (Pearson r and VIF) on
# the trial-level multivariable predictor set, as an R-side mirror of the
# Python version.
#
# Author: Kerem Peker (ANR 2106332), Tilburg University CSAI BSc, 2026.
# ============================================================

suppressPackageStartupMessages({
  library(lme4)
  library(car)        # for vif()
})

# ------------------------------------------------------------
# Portable path resolution (Rscript / source / R -<- script.R)
# ------------------------------------------------------------
.find_script_dir <- function() {
  args <- commandArgs(trailingOnly = FALSE)
  file_arg <- grep("--file=", args, value = TRUE)
  if (length(file_arg)) {
    return(dirname(normalizePath(sub("--file=", "", file_arg[1]))))
  }
  ofile <- tryCatch(sys.frame(1)$ofile, error = function(e) NULL)
  if (!is.null(ofile)) return(dirname(normalizePath(ofile)))
  getwd()
}
.script_dir <- .find_script_dir()
.candidates <- c(
  file.path(.script_dir, "..", "sample_data", "thesis_trial_data.csv"),
  file.path(.script_dir, "..", "thesis_trial_data.csv"),
  file.path(.script_dir, "thesis_trial_data.csv")
)
.csv_path <- .candidates[file.exists(.candidates)][1]
if (is.na(.csv_path)) stop(sprintf(
  "Cannot find thesis_trial_data.csv. Looked in:\n  %s",
  paste(.candidates, collapse = "\n  ")))
df <- read.csv(.csv_path)

# ------------------------------------------------------------
# Derive the binary correctness variable, excluding the Likert-3 midpoint.
# ------------------------------------------------------------
df$correct <- with(df,
  ifelse(attr == 3, NA,
    ifelse((attr <= 2 & truth_AI == 1) | (attr >= 4 & truth_AI == 0), 1L, 0L)))

df$rid   <- factor(df$rid)
df$trial <- factor(df$trial)
df$truth <- factor(df$truth, levels = c("Human", "AI"))

cat("=========================================================\n")
cat(" lme4 CROSSED RANDOM-EFFECTS MODEL (H1 robustness)\n")
cat(" correct ~ truth + (1 | rid) + (1 | trial)\n")
cat("=========================================================\n\n")

# Forced-choice working subset
df_fc <- subset(df, !is.na(correct))
cat("Forced-choice subset: n =", nrow(df_fc),
    "trials,", nlevels(droplevels(df_fc$rid)), "participants,",
    nlevels(droplevels(df_fc$trial)), "stimuli.\n\n")

# ------------------------------------------------------------
# Crossed GLMM
# ------------------------------------------------------------
m_crossed <- glmer(correct ~ truth + (1 | rid) + (1 | trial),
                   data = df_fc, family = binomial(link = "logit"),
                   control = glmerControl(optimizer = "bobyqa",
                                          optCtrl = list(maxfun = 2e5)))
cat("=== Crossed GLMM summary ===\n")
print(summary(m_crossed))

# Intercept-only model (no fixed effect of truth) for LRT
m_null <- glmer(correct ~ 1 + (1 | rid) + (1 | trial),
                data = df_fc, family = binomial(link = "logit"),
                control = glmerControl(optimizer = "bobyqa",
                                       optCtrl = list(maxfun = 2e5)))
cat("\n=== Likelihood-ratio test for true source ===\n")
print(anova(m_null, m_crossed, test = "Chisq"))

# Random-effect variances
re_var <- VarCorr(m_crossed)
cat("\n=== Random-effect variances ===\n")
print(re_var)

# Marginal accuracy prediction at the typical intercept
intercept_logit <- fixef(m_crossed)[["(Intercept)"]]
truth_eff       <- fixef(m_crossed)[["truthAI"]]
p_human <- plogis(intercept_logit)
p_ai    <- plogis(intercept_logit + truth_eff)
cat(sprintf("\nMarginal predicted accuracy at population mean:\n"))
cat(sprintf("  P(correct | Human stimulus) = %.3f\n", p_human))
cat(sprintf("  P(correct | AI stimulus)    = %.3f\n", p_ai))
cat(sprintf("  Aggregate trial-level accuracy in data: %.3f (= 56.5%% target)\n",
            mean(df_fc$correct)))

# ------------------------------------------------------------
# COLLINEARITY (continuous predictors for the multivariable model)
# ------------------------------------------------------------
cat("\n\n=========================================================\n")
cat(" PREDICTOR COLLINEARITY (truth_AI, fluency_c, credibility_c)\n")
cat("=========================================================\n\n")

df_full <- df[, c("truth_AI", "fluency_c", "credibility_c")]
df_full <- na.omit(df_full)
cat("Pearson correlations:\n")
print(round(cor(df_full), 4))

# VIF via a simple OLS surrogate (predicting an arbitrary outcome to extract
# the design-matrix VIF, since lm-based vif applies to the linear predictor).
df_full$dummy <- rnorm(nrow(df_full))
m_aux <- lm(dummy ~ truth_AI + fluency_c + credibility_c, data = df_full)
cat("\nVariance inflation factors:\n")
print(round(vif(m_aux), 3))
cat("\nInterpretation: VIF < 5 is unproblematic; 5-10 is worth noting;\n")
cat("> 10 suggests serious multicollinearity.\n")

cat("\nDone.\n")
