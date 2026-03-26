# Documentation

## Status

- Current milestone: Milestone 6 - dashboard-first commercial repositioning and Vercel live deployment
- Completed milestones:
  - Milestone 1: durable memory, config, bootstrap contracts, and dual-runtime repo metadata aligned to the approved plan
  - Milestone 2: Python CLI surface and shared R wrappers implemented
  - Milestone 3: expanded analytics, README/report generation, demo media, and release-facing tables/figures implemented
  - Milestone 4: CI/release scaffolding validated, public repo created, `main` pushed, and `v0.1.0` released
  - Milestone 5: repo root cleaned into a product-first layout, `course_2016/` published as a structured archive, and the public README refreshed with a repository tree plus workflow architecture diagram
- Next milestone: commit and push the dashboard-first narrative plus Vercel deployment config, then confirm the repo homepage points at the live site
- Last updated: 2026-03-26

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
- Decision: make the top of `README.md` explicitly answer what the project is, why it matters, what solution it provides, how it differs from related work, and how the public can reuse it.
  Why: the repo is now a public-facing toolkit, so value proposition and reuse guidance need to be visible before readers reach the deeper benchmark and visualization sections.
- Decision: keep the release workflow repairable from `main` through `workflow_dispatch`, while still publishing assets to a specific existing release tag.
  Why: the original `v0.1.0` tag run failed due to workflow-level token permissions, so a manual recovery path is needed without having to move or recreate the tag.
- Decision: make the public root product-first and move historically important but non-runtime materials into `course_2016/`.
  Why: the repo homepage should read like a public toolkit first, while the 2016 course archive remains available in a dedicated, browsable surface.
- Decision: add a repository tree and a process/architecture diagram to the main README.
  Why: public users should be able to understand both the file layout and the end-to-end children’s literature workflow at a glance.
- Decision: frame the repo’s near-term business value as editorial/discovery intelligence rather than story-path prediction.
  Why: the current outputs are descriptive, comparative, and retrieval-oriented; they support editorial and recommendation workflows today, but they do not yet justify a strong forecasting claim about plot outcomes.
- Decision: make Libraries & EdTech the primary audience for the commercial narrative, with researchers/teachers and publishers/editors presented as secondary reuse audiences.
  Why: the current outputs already support title discovery, themed list building, similarity navigation, and catalog audit workflows more directly than they support manuscript prediction or market forecasting.
- Decision: position recommendation as one capability inside a broader dashboard product rather than as the entire product identity.
  Why: the repo already has multiple decision surfaces beyond similarity, including theme profiles, sentiment arcs, entity structure, and corpus bias audit panels.
- Decision: deploy the live website as a thin Vercel static surface over the generated `docs/index.html` report rather than rebuilding the repo into a new frontend app.
  Why: the current product is already most honest as a generated report/dashboard, so Vercel can expose it quickly without inventing a fake SaaS layer.
- Decision: keep exact corpus totals in the deeper dashboard/report, but use compact display values in the homepage `Collection Snapshot`.
  Why: landing-page KPI cards need to stay legible at common desktop widths; `1.33M` communicates scale cleanly while the exact count remains one click deeper.
- Decision: generate README hero media from real dashboard routes first, with the old analysis-figure carousel only as a fallback.
  Why: the public README should show the actual website product surface and key workflows rather than a disconnected rotation of analysis plots.

## Validation Log

- Command: `gh auth status`
  Result: authenticated to `github.com` as `bozliu` with `repo` and `workflow` scopes.
  Follow-up: safe to create the public repo and release from this machine.
- Command: `gh repo create bozliu/aarhus-childrens-literature-toolkit --public --source=. --remote=origin --push ...`
  Result: succeeded; public repo created and `main` pushed.
  Follow-up: remote `origin` now tracks the live public repository.
- Command: `gh release create v0.1.0 --repo bozliu/aarhus-childrens-literature-toolkit ...`
  Result: succeeded; release published with bundle/media/table assets.
  Follow-up: release URL is `https://github.com/bozliu/aarhus-childrens-literature-toolkit/releases/tag/v0.1.0`.
- Command: `git fetch --tags origin`
  Result: succeeded; local tag state now matches the remote release tag.
  Follow-up: local git view is fully synced to the published release.
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
- Command: `./scripts/run_r.sh scripts/render_readme.R`
  Result: succeeded after the README positioning update; `README.md` now includes public-facing sections for project definition, importance, solution framing, related-work differentiation, and reuse guidance.
  Follow-up: commit and push the regenerated README and its generator source together so the public repo stays in sync.
- Command: `gh run view 23500389218 --repo bozliu/aarhus-childrens-literature-toolkit --json ...` and `--log`
  Result: the failed `release` run for `v0.1.0` built assets successfully but failed on `Publish release assets` with `Resource not accessible by integration`; the job token only had read access to repository contents.
  Follow-up: update `.github/workflows/release.yml` to request `contents: write` and support manual tag-targeted reruns from `main`.
- Command: `gh workflow run release.yml --repo bozliu/aarhus-childrens-literature-toolkit --ref main -f tag=v0.1.0` followed by `gh run watch 23502021089 ...`
  Result: succeeded; the replacement `release` run on `main` rebuilt assets and completed `Publish release assets` for `v0.1.0`.
  Follow-up: the release is operational again, while the original historical red run remains as an immutable record of the pre-fix workflow.
- Command: `python3 -m py_compile childlit_toolkit/pipeline.py && python -m childlit_toolkit all`
  Result: succeeded after the product-first cleanup pass; manifests, figures, tables, `README.md`, `docs/report.qmd`, and `docs/index.html` were regenerated against the moved `course_2016/` paths.
  Follow-up: the public outputs now point to the structured 2016 archive instead of the old root-level historical paths.
- Command: `git ls-files | awk -F/ 'NF==1 {print}' | sort` and `rg -n "tm_the_great_unread-master/|other_resources/" README.md data/manifests/local_assets.csv`
  Result: the tracked root is now limited to product-facing essentials plus durable-memory files, and the generated inventory no longer reports the old root-level `tm_the_great_unread-master/` or `other_resources/` paths.
  Follow-up: the repo is ready to publish the cleaner top-level layout once the staged rename/add/delete set is committed.
- Command: `sed -n '35,78p' README.md` and `sed -n '389,442p' README.md`
  Result: verified that the public README now contains a children’s-literature workflow architecture diagram and a repository tree with purpose annotations for the public-facing structure.
  Follow-up: keep these sections generator-backed in `childlit_toolkit/pipeline.py` so future rebuilds stay consistent.
- Command: `git push origin main`
  Result: succeeded; commit `cc97667` is now on `origin/main` for `bozliu/aarhus-childrens-literature-toolkit`.
  Follow-up: GitHub accepted the push, but warned that `course_2016/slides/supplementary/latent_variables.pdf` is 51.86 MB, which is above the recommended 50 MB threshold while still below the hard 100 MB limit.
- Command: `python3 -m py_compile childlit_toolkit/pipeline.py && python -m childlit_toolkit render`
  Result: succeeded after the README commercial-positioning pass; the README/report sources were regenerated with explicit sections about what the repo can tell users, what it cannot yet predict, and why the strongest current product framing is editorial/discovery intelligence.
  Follow-up: commit the updated public narrative together with the generator source and project-memory files so the GitHub repo and durable-memory log stay aligned.
- Command: `python3 -m py_compile childlit_toolkit/pipeline.py` and `python -m childlit_toolkit report`
  Result: succeeded after the dashboard-first rewrite; `README.md`, `docs/report.qmd`, and the fallback `docs/index.html` now all describe the repo as a Libraries & EdTech children’s literature discovery dashboard with a concrete MVP and phased roadmap.
  Follow-up: deploy this generated report surface live rather than shipping only GitHub-hosted documentation.
- Command: `vercel project add aarhus-childrens-literature-toolkit --scope bozlius-projects`, `vercel link --yes --project aarhus-childrens-literature-toolkit --scope bozlius-projects`, and `vercel deploy --prod -y --scope bozlius-projects --logs`
  Result: succeeded; the live production alias is `https://aarhus-childrens-literature-toolkit.vercel.app`.
  Follow-up: set the GitHub repo homepage to the Vercel alias and keep `.vercelignore`/`vercel.json` in the repo so future deploys preserve the same public URL.
- Command: `gh repo edit bozliu/aarhus-childrens-literature-toolkit --homepage https://aarhus-childrens-literature-toolkit.vercel.app`
  Result: succeeded; the GitHub repo homepage now points at the live Vercel site.
  Follow-up: future public references can use the stable alias instead of the one-off deployment URL.
- Command: `python -m childlit_toolkit report`
  Result: succeeded after the homepage KPI refinement and site-driven hero-media upgrade; `site/`, `public/`, `README.md`, `docs/index.html`, and `results/assets/hero.gif` / `hero.mp4` were regenerated together.
  Follow-up: the public README demo now reflects real website routes instead of only static chart assets.
- Command: `vercel deploy --prod -y --scope bozlius-projects` from `public/`
  Result: succeeded; the production alias `https://aarhus-childrens-literature-toolkit.vercel.app` now serves the compact homepage KPI cards and refreshed hero media.
  Follow-up: keep the `public/` deploy surface in sync via the report pipeline before future production deploys.
- Command: Chrome DevTools production screenshot check on `https://aarhus-childrens-literature-toolkit.vercel.app/`
  Result: confirmed the main-page `Collection Snapshot` no longer overflows and now displays `Words` as `1.33M` within the stable 2x2 metric grid.
  Follow-up: no additional homepage layout repair is required for the current desktop breakpoint.
- Command: `gh run view --repo bozliu/aarhus-childrens-literature-toolkit 23597390394 --job ... --log`
  Result: both failing CI jobs (`python-smoke` and `macos-dual-runtime-smoke`) failed for the same reason: `python -m childlit_toolkit smoke` reported missing required files `site/index.html` and `public/index.html`.
  Follow-up: repair `.gitignore` so generated route HTML under `site/` and `public/` is tracked, then recommit those files and rerun CI.
- Command: `python -m childlit_toolkit smoke`, `python -m py_compile childlit_toolkit/pipeline.py childlit_toolkit/cli.py inst/python/build_assets.py`, and `Rscript -e "source('R/utils.R'); cat('R + Python interface files are present\n')"`
  Result: all local equivalents of the failing CI smoke checks passed after unignoring and staging the missing route HTML files.
  Follow-up: push the CI repair to `main` and let the workflow re-run on the new commit.

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
- Issue 3: `dl` currently sees `Rscript` through the machine path rather than a conda-installed R runtime.
  Impact: the project runs correctly through the `dl` workflow on this machine, but a stricter fully-conda R story remains an optional follow-up.
- Issue 4: the original `v0.1.0` release workflow run is permanently red in GitHub history.
  Impact: that historical run used the old workflow definition from the tag commit, so it cannot inherit the repaired permissions; the practical fix is to dispatch a new successful release run from `main`.
- Issue 5: `course_2016/slides/supplementary/latent_variables.pdf` is larger than GitHub’s recommended file size.
  Impact: the file is published successfully, but it may be worth replacing with a smaller archival copy or Git LFS if the repo should minimize clone weight.
- Issue 6: the first Vercel production attempt uploaded only `vercel.json` because the initial `.vercelignore` allowlist was too aggressive.
  Impact: the issue was fixed in the same session by switching `.vercelignore` to a blacklist-style deploy filter and redeploying the same production alias.

## Follow-Ups

- Follow-up 1: optionally install `sentence_transformers`, `bertopic`, and `gliner` in `dl` to replace the current fallback backends.
- Follow-up 2: optionally install system Quarto and rerender `docs/index.html` from `docs/report.qmd`.
- Follow-up 3: optionally tighten the public corpus inventory further if a smaller curated validation pack is preferred over the full `LancsBox` corpora subset.
- Follow-up 4: optionally configure explicit global git author name/email before the next release commit.
