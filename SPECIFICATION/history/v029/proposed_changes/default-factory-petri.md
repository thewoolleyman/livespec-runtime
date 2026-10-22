---
topic: default-factory-petri
author: claude-opus-5-5
created_at: 2026-10-22T22:17:31Z
---

## Proposal: Default factory is petri

### Target specification files

- constraints.md

### Summary

In constraints.md §"Factory routing", change the default-factory sentence from requiring `legacy` to requiring `petri`, and state that `legacy` remains a declared registry-backed entry. Every other sentence of the section (registry-backed entries, no server, no docker_host, registry-bound resolution) is unchanged.

### Motivation

Maintainer direction relayed by coordinator session gitops-fleet-capacity-monitoring as ruling R668 cuts this repository's dispatch default over from the `legacy` Fabro factory to `petri`, the current Fabro server; ruling R672 approves this spec revise as a delegated decision. Work-item bd-ib-iud52v. The committed .livespec.jsonc now declares a registry-backed `petri` entry and sets `"default_factory": "petri"`, keeping `legacy` declared; the orchestrator's resolver resolves `petri` through /etc/livespec/fabro-factories.json. The ratified sentence still names `legacy`, so the spec must move with the configuration.

### Proposed Changes

In constraints.md §"Factory routing", replace the final sentence

`dispatcher.default_factory` MUST name `legacy`.

with

`dispatcher.default_factory` MUST name `petri`; `legacy` remains a declared registry-backed entry.

No other text in the section changes, and no `## ` heading is added, renamed or removed.
