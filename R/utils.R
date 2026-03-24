`%||%` <- function(x, y) {
  if (is.null(x) || length(x) == 0) y else x
}

project_root <- function() {
  normalizePath(".", winslash = "/", mustWork = TRUE)
}

read_project_config <- function(path = "config/project.yml") {
  runtime_env <- Sys.getenv("CHILDLIT_RUNTIME_ENV", unset = "dl")
  if (requireNamespace("yaml", quietly = TRUE) && file.exists(path)) {
    return(yaml::read_yaml(path))
  }
  list(project = list(default_runtime_env = runtime_env))
}

default_runtime_env <- function() {
  config <- read_project_config()
  config$project$default_runtime_env %||% "dl"
}

ensure_parent_dir <- function(path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  invisible(path)
}

write_csv_safe <- function(x, path) {
  ensure_parent_dir(path)
  utils::write.csv(x, path, row.names = FALSE)
  invisible(path)
}

ensure_python_backend <- function() {
  if (Sys.which("conda") == "") {
    stop("Conda is required for the shared Python backend.", call. = FALSE)
  }
  invisible(TRUE)
}

run_python_backend <- function(args, env = NULL) {
  env <- env %||% default_runtime_env()
  ensure_python_backend()
  cmd <- c("run", "-n", env, "python", "-m", "childlit_toolkit", args)
  status <- system2("conda", cmd)
  if (!identical(status, 0L)) {
    stop("Python backend failed for args: ", paste(args, collapse = " "), call. = FALSE)
  }
  invisible(status)
}
