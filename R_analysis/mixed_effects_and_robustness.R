# ============================================================
# Mixed-effects ordinal regression + Brant test + robustness
# Addresses reviewer feedback (clustered SEs, PO assumption, Likert-3 handling)
# ============================================================
suppressPackageStartupMessages({
  library(ordinal)
  library(brant)
  library(MASS)
})

# Resolve data path relative to this script so the archive is portable.
# Supports three invocation modes: `Rscript script.R`, `source("script.R")`,
# and `R --no-save < script.R` (in which case cwd is the fallback).
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
df$attribution <- factor(df$attr, levels = 1:5, ordered = TRUE)
df$truth      <- factor(df$truth, levels = c("Human", "AI"))   # AI = reference contrast
df$rid        <- factor(df$rid)
df$trial      <- factor(df$trial)
df$fluency_c     <- scale(df$fluency, scale = FALSE)[, 1]
df$credibility_c <- scale(df$credibility, scale = FALSE)[, 1]

cat("========================================\n")
cat(" MIXED-EFFECTS ORDINAL LOGISTIC REGRESSION\n")
cat(" Random intercepts: participant (rid) + stimulus (trial)\n")
cat("========================================\n\n")
m_mixed <- clmm(attribution ~ truth + fluency_c + credibility_c +
                  (1 | rid) + (1 | trial),
                data = df, link = "logit")
print(summary(m_mixed))

co <- summary(m_mixed)$coefficients
cat("\nOdds ratios (mixed-effects):\n")
for (pred in c("truthAI", "fluency_c", "credibility_c")) {
  if (pred %in% rownames(co)) {
    beta <- co[pred, "Estimate"]
    se   <- co[pred, "Std. Error"]
    p    <- co[pred, "Pr(>|z|)"]
    cat(sprintf("  %s: beta = %+.3f, SE = %.3f, p = %.4f, OR = %.3f\n",
                pred, beta, se, p, exp(beta)))
  }
}

cat("\nVariance components:\n")
print(VarCorr(m_mixed))

# ------------------------------------------------------------
# Brant test for proportional-odds (uses MASS::polr fit since
# ordinal::clm does not have native brant integration)
# ------------------------------------------------------------
cat("\n========================================\n")
cat(" BRANT TEST FOR PROPORTIONAL-ODDS ASSUMPTION\n")
cat("========================================\n\n")
m_polr <- polr(attribution ~ truth + fluency_c + credibility_c,
               data = df, method = "logistic", Hess = TRUE)
brant_res <- brant::brant(m_polr)
cat("\nInterpretation: p > .05 supports the proportional-odds assumption.\n")

# ------------------------------------------------------------
# Likert-3 robustness analyses (3 alternative codings)
# ------------------------------------------------------------
cat("\n========================================\n")
cat(" LIKERT-3 EXCLUSION ROBUSTNESS\n")
cat("========================================\n\n")

n_total  <- nrow(df)
n_forced <- sum(df$attr != 3)

# Strategy 1: original forced-choice (Likert-3 excluded)
correct_forced <- sum((df$attr <= 2 & df$truth_AI == 1) |
                      (df$attr >= 4 & df$truth_AI == 0))
cat(sprintf("Strategy 1 (forced-choice, original): %d/%d = %.3f\n",
            correct_forced, n_forced, correct_forced / n_forced))

# Strategy 2: Liberal-AI (Likert-3 counted as AI judgment)
correct_lib_ai <- sum((df$attr <= 3 & df$truth_AI == 1) |
                      (df$attr >= 4 & df$truth_AI == 0))
cat(sprintf("Strategy 2 (Likert-3 = AI judgment): %d/%d = %.3f\n",
            correct_lib_ai, n_total, correct_lib_ai / n_total))

# Strategy 3: Liberal-Human (Likert-3 counted as Human judgment)
correct_lib_hu <- sum((df$attr <= 2 & df$truth_AI == 1) |
                      (df$attr >= 3 & df$truth_AI == 0))
cat(sprintf("Strategy 3 (Likert-3 = Human judgment): %d/%d = %.3f\n",
            correct_lib_hu, n_total, correct_lib_hu / n_total))

# Strategy 4: Likert-3 counted as half-correct (continuity-adjusted)
correct_half  <- correct_forced + 0.5 * (n_total - n_forced)
cat(sprintf("Strategy 4 (Likert-3 = .5 credit): %.1f/%d = %.3f\n",
            correct_half, n_total, correct_half / n_total))

binom_forced <- binom.test(correct_forced, n_forced, p = 0.5)
binom_half   <- binom.test(round(correct_half), n_total, p = 0.5)
cat(sprintf("\nForced-choice binomial vs chance: p = %.4g, 95%% CI [%.3f, %.3f]\n",
            binom_forced$p.value, binom_forced$conf.int[1], binom_forced$conf.int[2]))
cat(sprintf("Continuity-adjusted binomial:    p = %.4g, 95%% CI [%.3f, %.3f]\n",
            binom_half$p.value, binom_half$conf.int[1], binom_half$conf.int[2]))

cat("\nDone.\n")
