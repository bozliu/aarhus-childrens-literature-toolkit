optional_packages <- c(
  "targets", "tarchetypes", "yaml", "jsonlite", "readr",
  "tibble", "fs", "reticulate"
)

if (file.exists("/opt/homebrew/bin/gcc-15") && file.exists("/opt/homebrew/bin/g++-15")) {
  makevars_dir <- file.path(getwd(), ".R")
  makevars_path <- file.path(makevars_dir, "Makevars")
  dir.create(makevars_dir, recursive = TRUE, showWarnings = FALSE)
  writeLines(
    c(
      "CC=/opt/homebrew/bin/gcc-15",
      "CXX=/opt/homebrew/bin/g++-15",
      "CXX11=/opt/homebrew/bin/g++-15",
      "CXX14=/opt/homebrew/bin/g++-15",
      "CXX17=/opt/homebrew/bin/g++-15",
      "CXX20=/opt/homebrew/bin/g++-15"
    ),
    makevars_path
  )
  Sys.setenv(
    CC = "/opt/homebrew/bin/gcc-15",
    CXX = "/opt/homebrew/bin/g++-15",
    CXX11 = "/opt/homebrew/bin/g++-15",
    CXX14 = "/opt/homebrew/bin/g++-15",
    CXX17 = "/opt/homebrew/bin/g++-15",
    CXX20 = "/opt/homebrew/bin/g++-15",
    R_MAKEVARS_USER = normalizePath(makevars_path, winslash = "/", mustWork = TRUE)
  )
}

if (!requireNamespace("renv", quietly = TRUE)) {
  install.packages("renv", repos = "https://cloud.r-project.org")
}

options(download.file.method = "libcurl")
options(timeout = max(300, getOption("timeout")))

install_with_fallback <- function(packages) {
  if (length(packages) == 0) {
    return(invisible(NULL))
  }
  tryCatch(
    utils::install.packages(packages, repos = "https://cloud.r-project.org", type = "binary"),
    error = function(err) {
      message("Binary package install unavailable, retrying from source: ", conditionMessage(err))
      utils::install.packages(packages, repos = "https://cloud.r-project.org")
    }
  )
}

if (identical(Sys.getenv("CHILDLIT_BOOTSTRAP_FULL_R", unset = "0"), "1")) {
  missing <- optional_packages[!vapply(optional_packages, requireNamespace, logical(1), quietly = TRUE)]
  if (length(missing) > 0) {
    install_with_fallback(missing)
  }
} else {
  message("Skipping optional R package install. Set CHILDLIT_BOOTSTRAP_FULL_R=1 to install targets/reticulate helpers.")
}

if (requireNamespace("reticulate", quietly = TRUE) &&
    "py_require" %in% getNamespaceExports("reticulate")) {
  reticulate::py_require(c(
    "pandas", "matplotlib", "pillow", "pyyaml", "requests",
    "networkx", "numpy", "scikit-learn", "imageio"
  ))
}

tryCatch(
  renv::snapshot(prompt = FALSE),
  error = function(err) {
    message("renv snapshot skipped: ", conditionMessage(err))
  }
)
message("Bootstrap complete.")
