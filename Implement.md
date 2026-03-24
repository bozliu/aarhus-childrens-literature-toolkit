# Implement

## Runbook

1. Treat `Plan.md` as the execution source of truth.
2. Complete one milestone at a time.
3. Keep diffs scoped to the current milestone.
4. Run milestone validation commands immediately after implementation.
5. Fix failures before moving on.
6. Update `Documentation.md` continuously with status, decisions, verification results, and release notes.
7. If the user changes scope, update `Prompt.md`, `Plan.md`, and `Documentation.md` before continuing.

## Working Agreements

- Preserve unrelated user changes and the historically meaningful 2016 archive material unless a public-release constraint requires excluding a file from version control.
- Prefer additive restructuring and explicit shared contracts over rewrites that hide provenance.
- Keep R and Python public interfaces symmetrical wherever practical: same commands, same config, same output paths.
- Use `reticulate` deliberately so R users can access optional Python-backed modules without changing workflows.
- Keep the repo reviewable and release-ready at each milestone boundary, including docs, CI, and packaging metadata.
