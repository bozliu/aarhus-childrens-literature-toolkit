# Prompt

## Project

- Name: Aarhus Children’s Literature Toolkit
- Root: /Users/bozliu/Movies/Aarhus Summer School/Academic
- Primary owner: bozliu
- Public release target: `bozliu/aarhus-childrens-literature-toolkit`

## Goal

- Primary objective: Rebuild the 2016 Aarhus Summer University children’s literature text-mining project into a dual-runtime public repository where R and Python are equal first-class entrypoints over the same manifests, results, and release assets.
- Current implementation objective: Reposition the public repo narrative around a dashboard-first children’s literature product for Libraries & EdTech, make the generated report/dashboard live on Vercel, and keep recommendation/discovery as a feature layer inside that dashboard while preserving research/DH value as a secondary proof surface.
- Current implementation objective: Reconnect to the user-owned Figma Make file, use it as the canonical UI reference, and restyle the live Vercel dashboard so it matches the Figma information architecture and visual direction while preserving the repo’s real-data routes, analytics features, and public-product framing.
- Intended audience or user: Libraries, reading platforms, curriculum/reading products, and title-discovery teams first; researchers, teachers, publishers, and editors second.

## Deliverables

- Deliverable 1: A reproducible dual-runtime project with shared manifests, `targets`-based R entrypoints, Python CLI entrypoints, and synchronized output contracts.
- Deliverable 2: A public-release documentation surface with `README.md`, `README.Rmd`, a Quarto HTML report in `docs/`, dense visual analytics, benchmark tables, IEEE-style references, a root-level repository tree, and a children’s literature process/architecture diagram.
- Deliverable 3: A dashboard-first product narrative that clearly states the primary audience, the practical decisions the repo supports, the current capability boundaries, and the honest MVP product shape.
- Deliverable 4: Release-ready assets and repo metadata including CI, citation/community files, dependency/license audits, hero media, and a GitHub `v0.1.0` release bundle.
- Deliverable 5: A browsable `course_2016/` folder that contains the 2016 course slides, teaching code, project work, supporting resources, legacy outputs, and raw archives, with a detailed archive README and slide-level table of contents.
- Deliverable 6: A Figma-aligned public web UI that keeps the current real-data dashboard functionality, fixes current frontend overflow/responsive issues, refreshes the README hero media from the updated website, and republishes the changes to GitHub and Vercel.

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
- [ ] The repo root is cleaned up into a product-first public layout with historical materials moved out of the first level.
- [ ] `README.md` explicitly explains the project aim, why children’s literature was chosen, what the analysis contributes to the field, and where the `course_2016/` archive lives.
- [ ] `README.md` includes a public-friendly repository tree and a visual architecture/process diagram for the children’s literature workflow.
- [ ] `README.md` clearly explains what information the repo provides, why it is not yet a story-trajectory predictor, and what realistic commercial value/use case it supports today.
- [ ] `README.md` is explicitly dashboard-first for Libraries & EdTech, with recommendation framed as one capability inside a broader discovery/dashboard product.
- [ ] `docs/report.qmd` and rendered report include a concrete product roadmap: current capability, current limits, MVP dashboard shape, primary user workflow, phased roadmap, and a clear explanation of why story prediction is not yet justified.
- [ ] The current dashboard/report website is deployed live on Vercel with the repo homepage pointing at the stable production URL.
- [ ] `course_2016/README.md` provides a detailed course archive guide with slide deck table of contents and navigation indexes.
- [ ] The live Vercel site visually aligns with the latest accessible Figma Make design while keeping current real-data functionality.
- [ ] The reported frontend overflow problems on the Theme Analysis and Book Explorer routes are fixed.
- [ ] README hero media is regenerated from the updated website flows.

## Fixed Assumptions

- Assumption 1: `Corpus of gold.docx` defines the canonical 20-book legacy core corpus for the children’s literature project.
- Assumption 2: The modern public repo should foreground the reusable product path while preserving 2016 reproduction as a documented baseline layer.
- Assumption 3: The default public release should be honest and incremental, so the first published version is `v0.1.0`.
- Assumption 4: The repo’s honest MVP is a children’s literature discovery dashboard, not a standalone recommendation engine and not a story-forecasting system.
