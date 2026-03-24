# Contributing

## Principles

This repository is intended to be reusable as both a research workflow and a product-shaped public release. Contributions should improve reproducibility, interpretability, or release readiness without erasing the 2016 provenance trail.

## Before Opening a Pull Request

1. Keep changes scoped and explain whether they affect the legacy baseline, the modern pipeline, or the public-release surface.
2. Run the shared smoke path first.
3. If you add a new figure or table, update the README or report interpretation text so the output is meaningful to a public audience.
4. If you introduce a new dependency or model, document its license and commercial-use implications.

## Preferred Validation

- `make smoke`
- `make python-assets`
- `make readme`
- `make report`

## Style Notes

- Keep manifests and generated outputs stable.
- Prefer additive changes over destructive rewrites of archived material.
- Use the shared config/result schema rather than introducing one-off outputs.
