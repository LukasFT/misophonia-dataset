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

# show data
print(head(data))