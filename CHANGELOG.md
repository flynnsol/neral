# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - Unreleased

### Added

- `engineer` subagent: implements one ticket test-first inside its allowed paths, in one commit.
- `reviewer` subagent: read-only review of a diff through one lens.
- `verifier` subagent: tries to refute each finding with evidence.
- `tester` subagent: writes failing repro tests.
- `neral:review` pipeline skill: context pack, deterministic gate, parallel lens passes, verification, ranked P0-P3 report, capped fix loop.
- `/neral:config` command.
- `.neral/config.yml` and `.neral/learnings.md` configuration files.
- Support for ticket conventions (`role`, `touches`, `acceptance`).
