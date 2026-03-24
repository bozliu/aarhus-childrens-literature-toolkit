build_report_fragments <- function() {
  run_python_backend("modern")
  data.frame(
    fragment = c(
      "results/fragments/corpus_summary.md",
      "results/fragments/legacy_baseline.md",
      "results/fragments/modern_stack.md",
      "results/fragments/release_readiness.md"
    ),
    stringsAsFactors = FALSE
  )
}

render_readme <- function() {
  run_python_backend("render")
  invisible("README.md")
}

render_report <- function() {
  run_python_backend("report")
  invisible("docs/index.html")
}
