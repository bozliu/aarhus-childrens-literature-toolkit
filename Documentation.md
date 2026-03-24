# Documentation

## Status

- Current milestone: Milestone 4
- Completed milestones:
  - Milestone 1: durable memory, config, bootstrap contracts, and dual-runtime repo metadata aligned to the approved plan
  - Milestone 2: Python CLI surface and shared R wrappers implemented
  - Milestone 3: expanded analytics, README/report generation, demo media, and release-facing tables/figures implemented
- Next milestone: publish the public GitHub repo, push `main`, and create the `v0.1.0` release
- Last updated: 2026-03-25

## Decisions

- Decision: keep one shared result contract and let both R and Python entrypoints target the same manifests, figures, tables, and report outputs.
  Why: the public release goal is reuse, not maintaining two divergent pipelines.
- Decision: make the R public interface lightweight and base-R friendly, while keeping `targets`/`reticulate` as optional enhancements instead of hard runtime requirements.
  Why: this avoids blocking the R path on a large compiled-package install before users can run the project.
- Decision: treat system `Rscript` visible inside `conda run -n dl ...` as an acceptable practical runtime path on this machine.
  Why: it satisfies the user requirement that the project run under the `dl` workflow while avoiding unstable conda-side R installation.
- Decision: default report rendering to system Quarto only; otherwise fall back to generated HTML.
  Why: the bundled local `tools/` Quarto tree is not suitable for the public repo and should not be required for a successful release build.
- Decision: keep the modern default stack honest about availability.
  Why: the current local validation shows `transformers` and `torch` available, but `sentence_transformers`, `bertopic`, and `gliner` are still optional and presently missing, so the repo must surface the active fallback backends explicitly.

## Validation Log

- Command: `gh auth status`
  Result: authenticated to `github.com` as `bozliu` with `repo` and `workflow` scopes.
  Follow-up: safe to create the public repo and release from this machine.
- Command: `make setup`
  Result: succeeded; `./scripts/setup_dl_runtime.sh` detected that `Rscript` is already available inside the `dl` runtime path.
  Follow-up: no conda-side R overlay install was required for this machine.
- Command: `./scripts/run_r.sh scripts/bootstrap.R`
  Result: succeeded with the lightweight path; optional heavy R packages were skipped by default and `renv.lock` is now present.
  Follow-up: `CHILDLIT_BOOTSTRAP_FULL_R=1` remains available for users who want the heavier optional R package stack.
- Command: `./scripts/run_r.sh scripts/run_targets.R modern`
  Result: succeeded and rebuilt the shared modern outputs from the R entrypoint.
  Follow-up: confirms the R interface can drive the shared pipeline without requiring `targets`.
- Command: `./scripts/run_r.sh scripts/render_readme.R`
  Result: succeeded and regenerated `README.md`.
  Follow-up: public-facing markdown is now aligned with the latest outputs.
- Command: `./scripts/run_r.sh scripts/render_report.R`
  Result: succeeded and regenerated `docs/index.html` via fallback HTML because system Quarto is not installed.
  Follow-up: `docs/report.qmd` remains the canonical report source; `docs/index.html` is still publishable.
- Command: `make readme`
  Result: succeeded.
  Follow-up: neutral `make` wrappers now work for README generation.
- Command: `make report`
  Result: succeeded.
  Follow-up: neutral `make` wrappers now work for report generation.
- Command: `make smoke`
  Result: succeeded.
  Follow-up: the public repo has a fast local smoke entrypoint.
- Command: `python3 -m py_compile childlit_toolkit/pipeline.py childlit_toolkit/cli.py childlit_toolkit/__main__.py inst/python/build_assets.py`
  Result: succeeded.
  Follow-up: Python packaging/CLI files are syntactically valid.

## How To Run Or Demo

- Preferred setup:
  - `make setup`
  - `make bootstrap`
- Python-first path:
  - `python -m childlit_toolkit modern`
  - `python -m childlit_toolkit render`
  - `python -m childlit_toolkit report`
- R-first path:
  - `./scripts/run_r.sh scripts/run_targets.R modern`
  - `./scripts/run_r.sh scripts/render_readme.R`
  - `./scripts/run_r.sh scripts/render_report.R`
- Neutral public interface:
  - `make modern`
  - `make readme`
  - `make report`
- Demo assets:
  - `results/assets/hero.gif`
  - `results/assets/hero.mp4`
  - `docs/index.html`
  - `README.md`

## Known Issues

- Issue 1: system Quarto is not installed on this machine.
  Impact: `docs/index.html` is generated via the fallback HTML path rather than an actual Quarto render.
- Issue 2: the modern local backends are only partially installed.
  Impact: the current validated runtime uses `afinn-fallback`, `tfidf-fallback`, and `heuristic-titlecase`; README and benchmark tables surface that honestly.
- Issue 3: the public repo and GitHub release have not yet been created.
  Impact: remote publishing is the only major remaining milestone.
- Issue 4: the repository has no committed baseline yet.
  Impact: the first commit must be curated carefully to avoid accidentally adding ignored local-only material.

## Follow-Ups

- Follow-up 1: create `bozliu/aarhus-childrens-literature-toolkit` as a public repo and push `main`.
- Follow-up 2: create tag `v0.1.0` and publish the GitHub release with README/report/media assets.
- Follow-up 3: optionally install `sentence_transformers`, `bertopic`, and `gliner` in `dl` to replace the current fallback backends.
- Follow-up 4: optionally install system Quarto and rerender `docs/index.html` from `docs/report.qmd`.
