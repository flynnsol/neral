<p align="center">
  <img src="assets/banner.png" alt="Neral" width="100%">
</p>

<p align="center">
  <img src="assets/logo.png" alt="Neral logo" width="96">
</p>

# Neral

A Claude Code plugin of `engineer`, `reviewer`, `verifier` and `tester` subagents, plus an evidence-first review pipeline.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Status: pre-release](https://img.shields.io/badge/status-pre--release-orange.svg)

## Description

Neral is a standalone Claude Code plugin that splits software work into small, focused roles. One agent implements, others review through a single lens, and findings only survive if they hold up against evidence. It works on its own, and it honours ticket conventions (`role`, `touches`, `acceptance`) so orchestration tools such as Engram can dispatch work to it.

> [!IMPORTANT]
> Neral is pre-release and contains no code yet. Everything below describes the planned v0.1.0.

## Features

Four subagents:

| Agent | What it does |
| ----- | ------------ |
| `engineer` | Implements one ticket test-first inside its allowed paths, in one commit. |
| `reviewer` | Read-only. Reviews a diff through one lens: correctness, security, data integrity, tests, performance or maintainability. |
| `verifier` | Tries to refute each finding with evidence before it is reported. |
| `tester` | Writes failing repro tests. |

One pipeline skill, `neral:review`:

1. Context pack for the change under review.
2. Deterministic gate.
3. Parallel lens passes, one reviewer per lens.
4. Verification of every finding by the `verifier`.
5. Ranked report, P0 to P3.
6. Capped fix loop.

Configuration:

- `.neral/config.yml` configures the pipeline.
- `.neral/learnings.md` holds project learnings carried between runs.
- `/neral:config` is the command for viewing and changing configuration.

## Getting Started

### Install

Coming in v0.1.0. There is no installable release yet.

### Usage

Usage instructions will be added with the v0.1.0 release.

## License

MIT.
