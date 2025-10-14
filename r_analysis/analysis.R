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

required_columns <- c("rating", "subject_uuid", "pair_uuid", "is_trig", "is_declared_trig", "order", "is_foams", "did_identify", "category")
missing_columns <- setdiff(required_columns, colnames(data))
if (length(missing_columns) > 0) {
  stop(paste("Missing required columns:", paste(missing_columns, collapse = ", ")))
}


# print("=== Debug data ===")
# decl_share <- with(data, tapply(is_declared_trig_pair, subject_uuid, mean))
# mean(decl_share); summary(decl_share)



# --- MAIN ANALYSIS ------------------------------------------------------------

cat("\n=== Linear mixed model (REML) ===\n")

# gmc <- function(x, g) x - ave(x, g, FUN = mean)   # group-mean center

m <- with(
  data,
  lmer(
    rating ~ 
      # Fixed effects:
      is_trig 
      + is_declared_trig
      + did_identify 
      + I(order - 1)
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


# # ---- ESTIMANDS VIA lmerTest::contest (with full-length L) --------------------
# # Build a full-length contrast in the model's coefficient order
# .expand_L <- function(model, L_named) {
#   beta_names <- names(fixef(model))
#   L_full <- setNames(rep(0, length(beta_names)), beta_names)
#   unknown <- setdiff(names(L_named), beta_names)
#   if (length(unknown)) stop(paste("Unknown coefficient(s):", paste(unknown, collapse=", ")))
#   L_full[names(L_named)] <- as.numeric(L_named)
#   matrix(as.numeric(L_full), nrow = 1, dimnames = list(NULL, beta_names))
# }

# # Pull denominator df from contest()'s ANOVA-like output
# .get_den_df <- function(ct) {
#   df_tab <- as.data.frame(ct)
#   cn <- tolower(colnames(df_tab))
#   j <- which(grepl("den", cn) & grepl("df", cn))
#   if (!length(j)) stop("Could not parse denominator df from contest()")
#   as.numeric(df_tab[1, j[1]])
# }

# .do_contrast <- function(model, L_named, name, alpha = 0.05) {
#   L <- .expand_L(model, L_named)
#   beta <- fixef(model)
#   V <- vcov(model)  # covariance of fixed effects
#   est <- as.numeric(L %*% beta)
#   se  <- sqrt(as.numeric(L %*% V %*% t(L)))

#   # Satterthwaite df via lmerTest::contest
#   ct <- contest(model, L = L, joint = FALSE)
#   df <- .get_den_df(ct)

#   tval <- est / se
#   p    <- 2 * pt(abs(tval), df = df, lower.tail = FALSE)
#   crit <- qt(0.975, df)
#   lo   <- est - crit * se
#   hi   <- est + crit * se

#   data.frame(contrast = name, estimate = est, SE = se, df = df,
#              t = tval, p = p, lower.CL = lo, upper.CL = hi,
#              meets_0_25 = abs(est) >= 0.25,
#              row.names = NULL)
# }

# # --- Three contrasts of interest ---
# ctr_df <- do.call(rbind, list(
#   .do_contrast(m, c(is_trig = 1),                       "undeclared_vs_control"),
#   .do_contrast(m, c(is_declared_trig = 1),              "declared_minus_undeclared"),
#   .do_contrast(m, c(is_trig = 1, is_declared_trig = 1), "declared_vs_control")
# ))

# cat("\n=== Key contrasts (Satterthwaite df) ===\n")
# print(ctr_df)

# # # ---- ESTIMANDS VIA EMMEANS ---------------------------------------------------
# # # We want:
# # #  1) Undeclared trigger vs control:   (is_trig=1, is_declared_trig=0) - (0,0)
# # #  2) Declared trigger vs control:     (1,1) - (0,0)
# # #  3) Declared minus Undeclared:       (1,1) - (1,0)
# # #
# # # Other covariates are held at their observed means (population-level prediction).

# # rg <- ref_grid(
# #   m,
# #   at = list(
# #     is_trig = c(0, 1),
# #     is_declared_trig = c(0, 1),
# #     did_identify = mean(data$did_identify, na.rm = TRUE),
# #     order = mean(data$order, na.rm = TRUE),
# #     is_foams = mean(data$is_foams, na.rm = TRUE)
# #   ),
# #   cov.reduce = mean
# # )

# # emm <- emmeans(rg, ~ is_trig * is_declared_trig)

# # # Build contrasts robustly by row-matching (no reliance on ordering assumptions)
# # emm_df <- as.data.frame(emm)
# # I <- diag(nrow(emm))

# # pick <- function(trig, decl) I[which(emm_df$is_trig == trig & emm_df$is_declared_trig == decl), , drop = FALSE]

# # L <- rbind(
# #   undeclared_vs_control       = pick(1, 0) - pick(0, 0),  # global baseline trigger effect
# #   declared_vs_control         = pick(1, 1) - pick(0, 0),  # personalized total effect
# #   declared_minus_undeclared   = pick(1, 1) - pick(1, 0)   # incremental personalization
# # )

# # ctr <- contrast(emm, L, adjust = "none")

# # cat("\n=== Key contrasts (Satterthwaite df via lmerTest) ===\n")
# # print(ctr)
# # cat("\n=== 95% CIs for contrasts ===\n")
# # print(confint(ctr, level = 0.95))

# # # Practical significance flagging (threshold = 0.25 points)
# # thr <- 0.25
# # ctr_df <- as.data.frame(ctr)
# # ctr_df$meets_0_25 <- abs(ctr_df$estimate) >= thr

# # cat("\n=== Practical significance check (|effect| >= 0.25) ===\n")
# # print(ctr_df[, c("contrast", "estimate", "SE", "df", "t.ratio", "p.value", "meets_0_25")])