args <- commandArgs(trailingOnly = TRUE)
mode <- if (length(args) == 0) "all" else args[[1]]

source("R/utils.R")
source("R/manifests.R")
source("R/legacy.R")
source("R/modern.R")
source("R/reporting.R")

run_base_mode <- function(mode) {
  switch(
    mode,
    legacy = build_legacy_summary(),
    modern = {
      build_corpus_manifest()
      build_local_assets()
      build_modern_outputs()
      build_report_fragments()
    },
    render = {
      build_report_fragments()
      render_readme()
      render_report()
    },
    all = {
      build_corpus_manifest()
      build_local_assets()
      build_legacy_summary()
      build_modern_outputs()
      build_report_fragments()
      render_readme()
      render_report()
    },
    stop("Unknown run mode: ", mode, call. = FALSE)
  )
}

if (!requireNamespace("targets", quietly = TRUE)) {
  run_base_mode(mode)
  quit(save = "no", status = 0)
}

target_names <- switch(
  mode,
  legacy = c("legacy_summary"),
  modern = c("corpus_manifest", "local_assets", "modern_outputs", "report_fragments"),
  render = c("report_fragments", "readme_output", "report_output"),
  all = NULL,
  NULL
)

if (is.null(target_names) && !mode %in% c("all")) {
  stop("Unknown run mode: ", mode, call. = FALSE)
}

targets::tar_make(names = target_names)
