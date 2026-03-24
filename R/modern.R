build_modern_outputs <- function() {
  run_python_backend("modern")
  data.frame(
    figure = c(
      "results/figures/corpus_timeline.png",
      "results/figures/provenance_coverage.png",
      "results/figures/core_book_lengths.png",
      "results/figures/chunking_risk.png",
      "results/figures/author_gender_mix.png",
      "results/figures/sentiment_trajectories.png",
      "results/figures/topic_prevalence_heatmap.png",
      "results/figures/embedding_book_map.png",
      "results/figures/entity_network.png",
      "results/figures/auxiliary_validation_panel.png"
    ),
    table = c(
      "results/tables/corpus_manifest_overview.csv",
      "results/tables/benchmark_overview.csv",
      "results/tables/benchmark_sota_comparison.csv",
      "results/tables/dataset_inventory_summary.csv",
      "results/tables/sentiment_window_summary.csv",
      "results/tables/theme_prevalence_by_book.csv",
      "results/tables/embedding_neighbors.csv",
      "results/tables/entity_leaderboard.csv",
      "results/tables/auxiliary_validation_summary.csv",
      "results/tables/dependency_license_audit.csv"
    ),
    stringsAsFactors = FALSE
  )
}
