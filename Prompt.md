# Prompt

## Project

- Name: Aarhus Children’s Literature Toolkit
- Root: /Users/bozliu/Movies/Aarhus Summer School/Academic
- Primary owner: bozliu
- Public release target: `bozliu/aarhus-childrens-literature-toolkit`

## Goal

- Primary objective: Rebuild the 2016 Aarhus Summer University children’s literature text-mining project into a dual-runtime public repository where R and Python are equal first-class entrypoints over the same manifests, results, and release assets.
- Intended audience or user: Public GitHub users, digital humanities researchers, text mining practitioners, and commercial teams who want a reusable SOP for analyzing children’s literature corpora with local methods.

## Deliverables

- Deliverable 1: A reproducible dual-runtime project with shared manifests, `targets`-based R entrypoints, Python CLI entrypoints, and synchronized output contracts.
- Deliverable 2: A public-release documentation surface with `README.md`, `README.Rmd`, a Quarto HTML report in `docs/`, dense visual analytics, benchmark tables, and IEEE-style references.
- Deliverable 3: Release-ready assets and repo metadata including CI, citation/community files, dependency/license audits, hero media, and a GitHub `v0.1.0` release bundle.

## Non-Goals

- Out of scope item 1: Turning the repository into a hosted SaaS product in this pass.
- Out of scope item 2: Guaranteeing byte-for-byte identical reproduction of every stochastic 2016 topic-model run.

## Constraints

- Platform or runtime: The repo must run in both R and Python, with the local `dl` conda environment as the default managed runtime. R users should still be able to reach Python-backed modules through `reticulate`.
- Tools or dependencies: Prefer local, commercial-friendly, open-weight or open-source methods. Use current Project Gutenberg texts with provenance when local raw corpus files are missing.
- Performance, determinism, UX, or safety constraints: Default workflows should remain local, reproducible, and safe for public release. Heavy backends must degrade gracefully when optional dependencies are unavailable.
- Release constraints: The public repo should be releaseable under Apache-2.0, include clear setup instructions, avoid hidden paid APIs, and keep demo/media assets GitHub-friendly.

## Done When

- [ ] Durable memory files reflect the approved dual-runtime public-release scope.
- [ ] `dl` contains both Python and `R`/`Rscript`, and the repo documents how to bootstrap both language paths.
- [ ] R and Python expose first-class entrypoints for bootstrap, inventory/manifest generation, legacy rebuild, modern analysis, and rendering.
- [ ] Shared manifests and result outputs remain single-source and language-neutral.
- [ ] The repo produces additional visual analytics, benchmark tables, and a Quarto HTML report under `docs/`.
- [ ] Public-release metadata, CI, citation/community docs, and dependency/license audit artifacts are present.
- [ ] The repo is pushed to `bozliu/aarhus-childrens-literature-toolkit` and tagged/released as `v0.1.0`.

## Fixed Assumptions

- Assumption 1: `Corpus of gold.docx` defines the canonical 20-book legacy core corpus for the children’s literature project.
- Assumption 2: The modern public repo should foreground the reusable product path while preserving 2016 reproduction as a documented baseline layer.
- Assumption 3: The default public release should be honest and incremental, so the first published version is `v0.1.0`.
