library(lme4)
library(lmerTest)
library(emmeans)

# get the first argument of the script
args <- commandArgs(trailingOnly = TRUE)
print(args)


if (length(args) > 0) {
  path <- args[1]
} else {
  path <- "/data/dummy_data.csv"
  print(paste("No path provided, using default:", path))
}

data <- read.csv(path)
M_trials <- 12 # Used to center the order
foams_ratio = 0.2 # Used to check data balance

required_columns <- c("rating", "subject_uuid", "pair_uuid", "is_trig", "is_declared_trig", "order", "is_foams", "category")
missing_columns <- setdiff(required_columns, colnames(data))
if (length(missing_columns) > 0) {
  stop(paste("Missing required columns:", paste(missing_columns, collapse = ", ")))
}




print("=== Debug data ===")
print("Number of trials per subject (assumed):")
print(M_trials)
print("Expected FOAMS ratio:")
print(foams_ratio)
print("Data head")
print(head(data))
decl_share <- with(data, tapply(is_declared_trig_pair, subject_uuid, mean))
mean(decl_share); summary(decl_share)



# --- MAIN ANALYSIS ------------------------------------------------------------

cat("\n=== Linear mixed model (REML) ===\n")

# gmc <- function(x, g) x - ave(x, g, FUN = mean)   # group-mean center

data$order_centered <- data$order - (M_trials + 1) / 2

m <- with(
  data,
  lmer(
    rating ~
      # Fixed effects:
      is_trig
      + is_declared_trig
      + order_centered
      + is_foams
      # Random effects:
      + (1 + is_trig || subject_uuid)
      + (1 + is_trig || pair_uuid)
      ,
    data = data,
    REML = TRUE,
    control = lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e5))
  )
)


print(summary(m))

# # Print random effects (will be very long)
# cat("\n=== Random effects ===\n")
# print(ranef(m, condVar = TRUE))

# 95% Wald CIs for fixed effects (quick, stable)
all_ci <- confint(m, method = "Wald")
fe_names <- names(fixef(m))
ci_fixed <- all_ci[rownames(all_ci) %in% fe_names, , drop = FALSE]

cat("\n=== 95% Wald CIs for fixed effects ===\n")
print(ci_fixed)

# Convergence / singularity diagnostics
if (isSingular(m, tol = 1e-5)) {
  cat("\n[Note] Model fit is singular (some random-effect variance ~ 0). "
      ,"Interpret random slopes with caution.\n", sep = "")
}
if (length(m@optinfo$conv$lme4) || length(m@optinfo$conv$opt)) {
  cat("\n[Note] Optimizer reported convergence warnings. Inspect m@optinfo.\n")
}


# --- ESTIMANDS ----------------------------------------------------------------
# We compute:
#   Delta_personal = beta_isTrig + beta_isDeclaredTrig + phi * beta_isFOAMS
#   Delta_global   = beta_isTrig + psi * beta_isDeclaredTrig + phi * beta_isFOAMS
# where:
#   phi = proportion of trigger trials that are FOAMS-sourced in the dataset
#   psi = share of trigger trials that belong to a subject's declared categories (empirical)

cat("\n=== Estimands (personalized and global) ===\n")

# Safeguards for division by zero if no trigger trials present
n_trig <- sum(data$is_trig == 1, na.rm = TRUE)
if (n_trig == 0) {
  stop("No trigger trials (is_trig==1) found; cannot compute psi or estimands.")
}

psi_hat <- with(data, sum(is_trig == 1 & is_declared_trig == 1, na.rm = TRUE) / n_trig)

cat(sprintf("phi (FOAMS share among trigger trials)  = %.4f\n", foams_ratio))
cat(sprintf("psi (Declared share among trigger trials)= %.4f\n", psi_hat))

# Pull fixed effects and covariance
beta <- fixef(m)
V <- vcov(m)

# Ensure required coefficients exist
needed <- c("(Intercept)", "is_trig", "is_declared_trig", "order_centered", "is_foams")
missing_beta <- setdiff(needed, names(beta))
if (length(missing_beta) > 0) {
  stop(paste("Model is missing fixed effects needed for estimands:", paste(missing_beta, collapse = ", ")))
}

# Build contrast vectors aligned to beta's order
L_zero <- setNames(rep(0, length(beta)), names(beta))

L_personal <- L_zero
L_personal["is_trig"] <- 1
L_personal["is_declared_trig"] <- 1
L_personal["is_foams"] <- foams_ratio

L_global <- L_zero
L_global["is_trig"] <- 1
L_global["is_declared_trig"] <- psi_hat
L_global["is_foams"] <- foams_ratio

# Helper to compute estimate, SE, CI, p-value via Wald normal
wald_from_L <- function(L, beta, V, level = 0.95) {
  est <- sum(L * beta)
  se <- sqrt(as.numeric(t(L) %*% V %*% L))
  z <- ifelse(se > 0, est / se, NA_real_)
  alpha <- 1 - level
  zcrit <- qnorm(1 - alpha/2)
  ci_lo <- est - zcrit * se
  ci_hi <- est + zcrit * se
  p <- ifelse(is.na(z), NA_real_, 2 * pnorm(-abs(z)))
  list(est = est, se = se, ci_lo = ci_lo, ci_hi = ci_hi, p = p)
}

res_personal <- wald_from_L(L_personal, beta, V, level = 0.95)
res_global   <- wald_from_L(L_global,   beta, V, level = 0.95)

# Pretty print results
fmt_row <- function(name, res) {
  sprintf(
    "%-18s  est = %.4f, SE = %.4f, 95%% CI [%.4f, %.4f], p = %.4g",
    name, res$est, res$se, res$ci_lo, res$ci_hi, res$p
  )
}

cat("\n--- Point estimates (Wald, treating psi as fixed) ---\n")
cat(fmt_row("Delta_personal", res_personal), "\n")
cat(fmt_row("Delta_global",   res_global),   "\n")

