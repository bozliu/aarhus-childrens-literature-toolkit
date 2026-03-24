# Security Policy

## Supported Release

The current supported public release line is `v0.1.x`.

## Reporting

If you find a security issue in scripts, automation, or bundled dependencies, open a private security report through GitHub if available, or contact the maintainer directly before public disclosure.

## Scope

This repository is designed for local analysis workflows. The highest-risk areas are:

- dependency supply-chain changes
- unsafe shell usage in helper scripts
- accidental publication of non-public local assets

## Response Goals

- acknowledge the report quickly
- assess reproducibility and blast radius
- patch and publish a release note when needed
