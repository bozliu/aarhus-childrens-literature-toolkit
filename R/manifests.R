load_corpus_seed <- function(path = "config/corpus_seed.csv") {
  utils::read.csv(path, stringsAsFactors = FALSE)
}

load_corpus_manifest <- function(path = "data/manifests/corpus_manifest.csv") {
  utils::read.csv(path, stringsAsFactors = FALSE)
}

build_corpus_manifest <- function() {
  run_python_backend("manifest")
  load_corpus_manifest()
}

load_local_assets <- function(path = "data/manifests/local_assets.csv") {
  utils::read.csv(path, stringsAsFactors = FALSE)
}

build_local_assets <- function() {
  run_python_backend("inventory")
  load_local_assets()
}
