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
#   Delta_personal = beta_isTrig + beta_isDeclaredTrig + foams_ratio * beta_isFOAMS
#   Delta_global   = beta_isTrig + psi_hat * beta_isDeclaredTrig + foams_ratio * beta_isFOAMS
# where:
#   foams_ratio = proportion of trigger trials that are FOAMS-sourced in the dataset (defined in the top)
#   psi_hat = share of trigger trials that belong to a subject's declared categories (empirical)

cat("\n=== Estimands (personalized and global) ===\n")

# Safeguards for division by zero if no trigger trials present
n_trig <- sum(data$is_trig == 1, na.rm = TRUE)
if (n_trig == 0) {
  stop("No trigger trials (is_trig==1) found; cannot compute psi or estimands.")
}

psi_hat <- with(data, sum(is_trig == 1 & is_declared_trig == 1, na.rm = TRUE) / n_trig)

print(paste("Estimated psi (share of declared triggers among trigger trials):", round(psi_hat, 4)))
print(paste("Foams ratio (phi):", round(foams_ratio, 4))) # defined in the top

# Fixed-effects order
beta_names <- names(fixef(m))
p <- length(beta_names)

# Helper: build a full-length named contrast row aligned to beta_names
L_row <- function(weights_named) {
  L <- setNames(rep(0, p), beta_names)
  for (nm in names(weights_named)) {
    if (!nm %in% beta_names) {
      stop(sprintf("Contrast references unknown coefficient: '%s'", nm))
    }
    L[nm] <- weights_named[[nm]]
  }
  # return as 1xP matrix
  matrix(L, nrow = 1, dimnames = list(NULL, beta_names))
}

# Define contrasts for the estimands
L_personal <- L_row(c(
  "is_trig" = 1,
  "is_declared_trig" = 1,
  "is_foams" = foams_ratio
))
L_global <- L_row(c(
  "is_trig" = 1,
  "is_declared_trig" = psi_hat,
  "is_foams" = foams_ratio
))

# Test each estimand using Satterthwaite df
res_personal <- contest(m, L_personal)
res_global   <- contest(m, L_global)


cat("\n--- Personalized estimand ---\n")
print(res_personal)

cat("\n--- Global estimand ---\n")
print(res_global)

# Also compute formatted summaries with estimate, SE, df, CI, p
beta <- fixef(m)
V    <- as.matrix(vcov(m))

summ_from_L <- function(L, res_from_contest, level = 0.95) {
  est <- as.numeric(L %*% beta)
  se  <- sqrt(as.numeric(L %*% V %*% t(L)))
  # Try to read denominator df from contest() output
  den_df <- suppressWarnings({
    if ("Den Df" %in% colnames(res_from_contest)) {
      as.numeric(res_from_contest[1, "Den Df"])
    } else if ("den.df" %in% names(res_from_contest)) {
      as.numeric(res_from_contest$den.df[1])
    } else NA_real_
  })
  tcrit <- qt(1 - (1 - level)/2, df = den_df)
  ci_lo <- est - tcrit * se
  ci_hi <- est + tcrit * se
  tval  <- est / se
  pval  <- 2 * pt(abs(tval), df = den_df, lower.tail = FALSE)
  list(est = est, se = se, df = den_df, lo = ci_lo, hi = ci_hi, p = pval)
}

rp <- summ_from_L(L_personal, res_personal)
rg <- summ_from_L(L_global,   res_global)

cat("\n=== Estimands (formatted; Satterthwaite) ===\n")
cat(sprintf("Delta_personal: est = %.4f, SE = %.4f, df = %.1f, 95%% CI [%.4f, %.4f], p = %.4g\n",
            rp$est, rp$se, rp$df, rp$lo, rp$hi, rp$p))
cat(sprintf("Delta_global:   est = %.4f, SE = %.4f, df = %.1f, 95%% CI [%.4f, %.4f], p = %.4g\n",
            rg$est, rg$se, rg$df, rg$lo, rg$hi, rg$p))