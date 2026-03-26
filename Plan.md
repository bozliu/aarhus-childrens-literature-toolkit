# Plan

## Summary

- Convert the current rebuild into a dual-runtime, public-release repository with shared manifests/results, deeper visual analytics, a Quarto report, CI, and a GitHub release.
- Complete a post-release productization pass that cleans the repo root, adds explicit children’s literature framing, and packages the 2016 Aarhus course materials into a structured archive.
- Clarify the repo’s analytical meaning and commercial value so the public README explains what the project does today, what it does not do, and which product direction best fits the current implementation.

## Architecture Notes

- Preserve the original 2016 source archive locally for provenance, but shape the public repo around reusable manifests, outputs, and documented workflows.
- Keep `config/project.yml` as the single configuration source for corpus, runtime, output, and release settings.
- Keep generated artifacts under stable shared locations: `data/manifests/`, `results/`, and `docs/`.
- Treat R and Python as equal public interfaces that call the same underlying contracts rather than maintaining separate result schemas.

## Milestones

### Milestone 1

- Goal: Align durable memory, repo metadata, and runtime/install contracts to the approved dual-runtime release plan.
- Scope: Update project memory, config, env specs, `Makefile`, bootstrap scripts, and top-level metadata so both language paths are first-class.
- Acceptance criteria: The repo documents the dual-runtime model clearly and exposes install/bootstrap hooks for both R and Python.
- Validation commands: `git diff -- Prompt.md Plan.md Implement.md Documentation.md Makefile config/project.yml`; runtime/help commands for the new entrypoints.

### Milestone 2

- Goal: Implement the Python package/CLI surface and strengthen the shared R wrappers.
- Scope: Add a `childlit_toolkit` Python package, expose `python -m childlit_toolkit ...` commands, add `reticulate::py_require()` support in R, and keep manifests/results shared.
- Acceptance criteria: R and Python entrypoints both resolve, and they target the same manifest/result paths.
- Validation commands: Python CLI help/smoke commands; R wrapper dry runs or smoke runs.

### Milestone 3

- Goal: Expand analytics, visual outputs, and report generation.
- Scope: Add new figures/tables/fragments, deeper benchmark outputs, Quarto report generation, hero/release media, and stronger README/report narratives.
- Acceptance criteria: README and `docs/index.html` render from generated shared assets and include interpretation text for all public visuals/tables.
- Validation commands: Asset-generation commands, report render, link checks by inspection, and smoke tests over generated files.

### Milestone 4

- Goal: Harden the repo for public release and publish it.
- Scope: Add CI, citation/community files, dependency/license audit output, release automation helpers, GitHub remote setup, commit/tag/release, and final validation.
- Acceptance criteria: CI config is present, repo metadata is publication-ready, GitHub remote exists, and `v0.1.0` is published with release assets.
- Validation commands: Local smoke suite, CI workflow lint-by-inspection, `git status --short`, `git remote -v`, and `gh release view v0.1.0`.

### Milestone 5

- Goal: Reorganize the repo into a product-first public layout and publish the 2016 course archive.
- Scope: Move historical root files into `course_2016/`, create `course_2016/README.md`, update README/report framing for children’s literature, add a root-level repo tree plus process/architecture diagram to the main README, and refresh inventory/reporting paths for the moved archive.
- Acceptance criteria: The root is clean, the archive is browsable on GitHub, README framing is field-specific, the repo tree and workflow diagram are visible on the public homepage, and generated manifests/docs reflect the new paths.
- Validation commands: `git status --short`; root directory inspection; asset/render commands; link checks by inspection; `git ls-files course_2016`.

### Milestone 6

- Goal: Make the public README explicit about analysis meaning, non-claims, and commercial value.
- Scope: Add README/report narrative that explains what information the repo provides for children’s literature, why the current implementation is descriptive/comparative rather than predictive, and why the most realistic near-term product direction is editorial/discovery intelligence rather than story forecasting.
- Acceptance criteria: A public reader can tell what business problem the repo can support today, what it cannot support yet, and why the current outputs are still commercially useful.
- Validation commands: `python3 -m py_compile childlit_toolkit/pipeline.py`; README render; top-of-README inspection; `git diff -- README.md childlit_toolkit/pipeline.py docs/report.qmd`.

## Stop-And-Fix Rule

- If a validation step fails, fix it before starting the next milestone.
- If scope changes, update `Prompt.md`, `Plan.md`, and `Documentation.md` before continuing.

## Decision Notes

- Decision 1: The repo remains R-led conceptually, but Python is elevated from backend-only support to a full first-class public interface.
- Decision 2: The `dl` conda environment remains the default managed runtime for both languages.
- Decision 3: The public repo name is `aarhus-childrens-literature-toolkit`, and the first public release is `v0.1.0`.
- Decision 4: The public repo root should be product-first, with the historical 2016 materials discoverable through `course_2016/` rather than scattered across the first level.
- Decision 5: The clearest near-term product framing is editorial and discovery intelligence for children’s literature, not direct story-path prediction.
