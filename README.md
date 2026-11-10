<p align="center">
  <img src="assets/banner.png" alt="Neral" width="100%">
</p>

# Neral

A Claude Code plugin of `engineer`, `reviewer`, `verifier` and `tester` subagents, plus an evidence-first review pipeline.

![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)
![Status: v0.1.0 in development](https://img.shields.io/badge/status-v0.1.0%20in%20development-orange.svg)

## Description

Neral is a standalone Claude Code plugin that splits software work into small, focused roles. One agent implements, others review through a single lens, and findings only survive if they hold up against evidence. It works on its own, and it honours ticket conventions (`role`, `touches`, `acceptance`) so orchestration tools such as Engram can dispatch work to it.

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

In Claude Code 2.1.275 or later, install in one step:

```text
/plugin install neral --marketplace flynnsol/neral
```

On older versions, add the marketplace first, then install the plugin:

```text
/plugin marketplace add flynnsol/neral
/plugin install neral@neral
```

### Usage

- **Agents.** `engineer`, `reviewer`, `verifier` and `tester` are ready to use as subagents. Engram's work skill picks one for each ticket based on the ticket's `role`.
- **Review.** Ask Claude to review a diff, a branch or a ticket, and the `neral:review` skill runs the pipeline and returns a ranked report.
- **Configuration.** Run `/neral:config` to view `.neral/config.yml`, or pass a subcommand to change it, for example `/neral:config profile strict`.
- **Pre-commit gate.** A Claude Code hook requires a passing quick review of the staged diff before Claude commits. Turn it off with `/neral:config precommit off`, or set `NERAL_REVIEW=off` for a session. It only covers commits Claude makes; commits made outside Claude are not checked.

## License

MIT.
