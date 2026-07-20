# policy-research-kit

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)

[한국어](README.md) · **English**

A [Claude Code](https://claude.com/claude-code) plugin: a **five-agent team** that takes a policy research report from research design to a submission-ready Korean `.hwpx` file.
The difference isn't prose quality — it's **verification by default**. The output tells you which figures were confirmed against primary sources and which are still unverified.

<!-- demo GIF goes here -->

## Why gates

Same request, same model, run through vanilla Claude Code and through this kit. A neutral third-party session then opened all 14 cited URLs from both and checked every figure against the source.

| | Vanilla | Kit |
|---|---|---|
| Cited sources actually opened | **0** | Every key figure |
| Numeric / attribution errors | **2** (all stated confidently) | **0** (unverified marked `[needs verification]`) |
| Process artifacts retained | 0/5 | **5/5** |

Vanilla writes better prose. The problem is that **nothing caught those two errors, and no record existed that could have.**

→ [Full audit](docs/vanilla-vs-kit.md) · [Why I built this + detailed usage](docs/why.md)

## Pipeline

```
Design → 🚦Gate 1 (design review) → ★You approve the outline
       → Research → Drafting → 🚦Gate 2 (5-axis review) → hwpx
```

Gate 1 protects **cost** (before 50 pages exist against the wrong outline); gate 2 protects against **overconfidence**.
The reviewer is a **different agent** from the writer and is read-only, so nobody signs off on their own work.

Caught in practice: 3 hallucinated sources · a 10× unit-conversion error · a population misreading · an overreaching research question downgraded.

## Install

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

## Usage

```
Write a policy research report on regional depopulation. Notes attached.   ← standard 50p+
Just a quick 4-page policy brief on this topic.                            ← brief mode
Review this 200-page report and shore up the weak sourcing.                ← existing report
Make chapter 3 center on international cases                               ← at the outline gate
```

It pauses twice (outline approval after gate 1, revision confirmation after gate 2), so you can step away in between.

## What you get

Not one document but **an auditable record set** — design, gate rulings, evidence ledger, review findings, fix log, final hwpx.
Which means that six months later, when someone asks where a figure came from, you can answer.

Worked examples: [standard, 65-page class](examples/policy-standard-demo/) · [brief](examples/policy-brief-demo/) · [vanilla baseline](examples/vanilla-baseline/)

## Requirements & limits

- `.hwpx` conversion needs the [kordoc](https://github.com/chrisryugj/kordoc) MCP server (without it the pipeline stops at Markdown)
- **Gates reduce errors; they don't eliminate them.** The reviewer shares a model family with the writer and can share its blind spots
- The A/B is a single run on a single topic — a reproducible case, not a statistical claim
- Shaped by Korean policy-research conventions (HWPX submission, Korean-language evidence)
- [Fallbacks, dependencies, keys](docs/runtime-notes.md) · [Gate design methodology](docs/verification-gates.md)

## Series

**Agent-team kits** — [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) (Korean government R&D proposals) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) (social science papers)

**Authoring & editing kits** — [lecture-deck-kit](https://github.com/parkjui92/lecture-deck-kit) (HTML lecture decks · live browser editing)

**Standalone skills** — [fact-verify](https://github.com/parkjui92/fact-verify) (source verification) · [paper-proofread](https://github.com/parkjui92/paper-proofread) (Korean academic proofreading) · [form-tailor](https://github.com/parkjui92/form-tailor) (institutional document formats) · [report-to-brief](https://github.com/parkjui92/report-to-brief) (report compression)

## License

[MIT](LICENSE). No proprietary institutional templates or real client deliverables included (bring-your-own-template).
