build_legacy_summary <- function() {
  run_python_backend("legacy")
  utils::read.csv("data/manifests/legacy_summary.csv", stringsAsFactors = FALSE)
}
