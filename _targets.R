library(targets)
tar_option_set(
  packages = c("fs", "jsonlite", "readr", "reticulate", "tibble", "yaml"),
  format = "rds"
)

source("R/utils.R")
source("R/manifests.R")
source("R/legacy.R")
source("R/modern.R")
source("R/reporting.R")

list(
  tar_target(project_config, read_project_config()),
  tar_target(corpus_manifest, build_corpus_manifest()),
  tar_target(local_assets, build_local_assets()),
  tar_target(legacy_summary, build_legacy_summary()),
  tar_target(modern_outputs, build_modern_outputs()),
  tar_target(report_fragments, build_report_fragments()),
  tar_target(readme_output, render_readme()),
  tar_target(report_output, render_report())
)
