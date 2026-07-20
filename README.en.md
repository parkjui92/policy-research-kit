# policy-research-kit

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)

[한국어](README.md) · **English**

> A [Claude Code](https://claude.com/claude-code) plugin: a **five-agent team** that takes a policy research report from research design all the way to a submission-ready Korean `.hwpx` file.
> What distinguishes this kit is not prose quality but **verification as the default** — the output tells you which figures were confirmed against primary sources and which are still unverified.

---

## Why I built this

Anyone who has asked an LLM to draft a policy research report has had the same experience. **The output is smooth.** The prose is good, the structure is plausible, and there are ten real, working URLs at the bottom. So it looks like a verified document.

The trouble starts when you actually open those URLs one by one:

- **Indicator confusion** — "AI service usage: 67.8% general population vs. 32.1% among older adults." The figure 67.8% is real. It just belongs to an entirely different indicator (digital literacy level among those 65+, 2023). This is not a fabricated number — it's a **real number attached to the wrong indicator**, which makes it *harder* to catch than an invented one.
- **Misattribution** — the cited research report doesn't contain the figure at all. I parsed the full 237-page PDF to confirm. The real source was a different survey by a different institution.
- And both errors were written in a **tone of certainty**. Nothing in the document signals to the reader that they should check.

This is not a model-quality problem. It's what happens when a process **attaches 10 citations while opening zero source documents**. Citations get completed from search-result snippets, so when they're wrong, nothing marks the spot.

In policy research this matters more than usual. Figures published in a report get re-cited, become budget justifications, and get read back to you in a legislative audit years later. "The AI wrote it that way" is not an available defense.

So what was needed was not better prose. It was **process**:

1. Something that stops you *before* you write 50 pages against the wrong outline
2. Something that checks claims against primary sources *after* drafting
3. A discipline that **marks unverified figures as unverified**

This kit is the result of bolting those pieces on, one at a time, while doing actual policy research work. It started as a personal harness; this is that harness cleaned up and published.

There's one more reason. Doing policy research in Korea means hitting two walls that international tools don't cross: **submissions must be in HWP/HWPX** (Hangul Word Processor, the de facto standard for Korean government documents), and **the key evidence lives in Korean-language databases** — KCI (Korea Citation Index), NKIS (national research institute reports), RISS — which international databases like CrossRef and Semantic Scholar simply don't index, so those sources come back as "unverifiable." This kit addresses both head-on.

---

## How it differs from vanilla Claude Code — a measured A/B

Claims that "custom agents beat vanilla" usually circulate without evidence. So I measured it. The **same request, the same underlying model**, run once through a vanilla session and once through this kit. Then a **neutral third-party audit session opened all 14 cited URLs from both outputs** and checked every figure against the source (including parsing that 237-page PDF in full).

| | A — Vanilla | B — Kit |
|---|---|---|
| Claims with a source attached | 60% (87% if end-of-doc list counts) | **100%, all inline** |
| Cited sources actually opened | **0** — cited from search snippets | Every key figure opened before citing |
| **Numeric / attribution errors** | **2, plus 1 year mix-up** | **0** |
| Tone on errors | Uniformly confident — no signal to the reader | Unverified figures explicitly downgraded with `[needs verification]` (5 places) |
| Process artifacts retained | 0 of 5 — one `.md` body | **5 of 5** — design, gate rulings, evidence ledger, review |
| Final format | `.md` | **`.hwpx`** |
| Prose and composition | **Better** — more polished, broader context, more current | Clear skeleton but thinner in length and specificity |

**The conclusion is not "vanilla is bad."** Vanilla produced the more readable draft. On prose it won outright, and it was more accurate on recent context. The problem is that **nobody caught the two errors in that draft, and there was no mechanism or record that could have.**

The kit is less polished. In exchange it answers "which figures in this document are confirmed and which are not," and hands you the evidence files behind that answer. For something you submit, the second thing matters more.

The full audit — including where vanilla won and where the kit was weak — is in [docs/vanilla-vs-kit.md](docs/vanilla-vs-kit.md). The prompts are published, so you can reproduce it yourself.

---

## Pipeline

```
Research design (designer)
  → 🚦 Gate 1: design review (reviewer mode 1, GO/NO-GO)
  → ★ You approve the outline  ← your intervention point
  → Evidence gathering (investigator, every fact sourced)
  → Drafting (writer, standard 50p+ / brief 4–8p)
  → 🚦 Gate 2: draft review (reviewer mode 2, five axes)
  → Korean conversion (hwpx-exporter, with quantitative self-check)
```

**Why two gates.** Gate 1 protects *cost* — once 50 pages exist against the wrong outline, there is no cheap way back. Gate 2 protects against *overconfidence* — a finished draft looks convincing, and it is hard to doubt your own text. The reviewer is a **different agent from the writer** and is read-only, which structurally prevents anyone from signing off on their own work.

What these gates have actually caught in practice: 3 hallucinated sources, a 10× unit-conversion error, a population misreading (a figure covering *all four* vulnerable groups written so it read as the older-adult value), and an overreaching research question ("compare effects" downgraded to "indicate direction" because the available evidence could not support the stronger claim).

---

## Install

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

Restart Claude Code and the orchestrator will pick up relevant requests automatically. Prompts can be in Korean or English; the report output is Korean-first.

---

## How to use it

### Scenario 1 — Standard report from scratch (50+ pages)

```
Write a policy research report on responses to regional depopulation.
Notes and statistics files attached.
```

It runs design → gate 1 → **outline approval** → research → drafting → gate 2 → hwpx. It pauses twice, so you can step away in between.

### Scenario 2 — Short policy brief (4–8 pages)

```
Just a quick 4-page policy brief on this topic.
```

Same team, same gates, but length, outline (background → issues → evidence → recommendations) and review axes switch to a lightweight mode. Good for advisory replies and R&D-brief formats.

### Scenario 3 — Review and strengthen an existing report

```
Review this 200-page report and shore up the weakly-sourced parts.
```

⚠️ **A caveat when feeding in an existing `.hwp`.** Text extraction from `.hwp` flattens tables and figures — in one case an original with 85 tables came back with 4. So this kit does *not* regenerate a replacement file from the extraction. It produces a **revision guide to apply to your original** as the primary deliverable, and it warns you that the reviewer may raise false positives about "empty tables."

### ★ Intervening at the outline approval gate

When the pipeline stops and shows you the outline, that is **the cheapest point at which to change direction**. Just say so:

```
Make chapter 3 center on international cases
Chapter 5 is too big — split alternatives from prioritization
Restructure the diagnosis around 8 sectors instead of 4 domains
```

The last one is a real restructuring that happened; the designer went back and rebuilt the framework around eight sectors.

### When the evidence doesn't convince you

```
Chapter 2's evidence is thin. Find more international statistics
Re-check the source for this figure
```

The investigator is designed to attach a source to every fact, so you can trace any sentence back through the evidence ledger (`03_evidence*.md`).

---

## What you get

Not one document — **an auditable record set**.

| File | Contents |
|---|---|
| `01_design.md` | Research design — RQ, analytical framework, outline |
| `02_design_gate.md` | Gate 1 ruling — what was flagged as [required] and why |
| `03_evidence*.md` | Evidence ledger — source per fact |
| `04_report_draft.md` | Body draft |
| `05_draft_review.md` · `05b_fix_log.md` | Gate 2 findings and what was actually changed |
| `06_report.hwpx` | Final submission file |

Which means that six months later, when someone asks where a figure came from, you can answer.

**Worked examples are included** — not trimmed-down demos, but full runs:

- [examples/policy-standard-demo/](examples/policy-standard-demo/) — full standard-mode run (65-page class, 8 chapters, 11 tables, 51 references). Gate 1 raised 4 [required] items; gate 2's 40-item sample cross-check found 0 mismatches; 69 of 69 tables survived hwpx conversion
- [examples/policy-brief-demo/](examples/policy-brief-demo/) — full brief-mode run
- [examples/vanilla-baseline/](examples/vanilla-baseline/) — the vanilla-side output from the A/B comparison

---

## The team

| Agent | Role | Skill |
|---|---|---|
| `policy-research-designer` | Intent analysis, RQ, framework, outline | `policy-research-design` |
| `policy-report-reviewer` | Design gate (mode 1) + draft review (mode 2) · **READ-ONLY** | `policy-report-review` |
| `policy-research-investigator` | Statistics, literature, domestic/international cases | `policy-research` (+ built-in geo-search) |
| `policy-report-writer` | Argument-driven body, reference list | `policy-report-writing` |
| `hwpx-exporter` | `.hwpx` conversion with quantitative self-verification | `rnd-hwpx-export` |

The orchestrator `rnd-policy-research-orchestrator` coordinates them and responds automatically to requests for policy reports, briefs, and issue papers.

> **Built-in geo-search.** Default web search is pinned to a US locale. The bundled wrapper searches in the target country's language and region (Japanese sources in Japanese), which is what it takes to reach local primary material. Without an API key it falls back to standard search.

---

## Requirements and fallbacks

- **`.hwpx` conversion** requires the [kordoc](https://github.com/chrisryugj/kordoc) MCP server. Without it, the pipeline still runs and stops at Markdown.
- **Without team-API support**, the same pipeline runs via sequential Agent calls. See the orchestrator's "public-release run notes."
- Setup, keys, and model selection: [docs/runtime-notes.md](docs/runtime-notes.md).

## Limitations

- **Gates reduce errors; they don't eliminate them.** The reviewer runs on a model from the same family as the writer and can share its blind spots. Final responsibility stays with a human.
- The A/B measurement is a **single run on a single topic**. It's a reproducible case, not a statistical claim.
- Paywalled sources (DBpia and similar) are held as ⚠️ when they can't be checked, rather than declared wrong.
- This kit is shaped by **Korean policy research conventions** (hwpx submission, Korean-language evidence, government statistics). In other contexts you'll want to adjust the outline templates and review axes.

## Further reading

- [docs/vanilla-vs-kit.md](docs/vanilla-vs-kit.md) — the full vanilla-vs-kit audit
- [docs/verification-gates.md](docs/verification-gates.md) — the two-stage gate design methodology, if you want to build your own
- [docs/runtime-notes.md](docs/runtime-notes.md) — fallbacks, dependencies, key setup

## Series

Sister kits and standalone skills built on the same design philosophy:

**Agent-team kits** — [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) (Korean government R&D proposals) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) (social science papers)

**Standalone skills** — [fact-verify](https://github.com/parkjui92/fact-verify) (source verification) · [paper-proofread](https://github.com/parkjui92/paper-proofread) (Korean academic proofreading) · [form-tailor](https://github.com/parkjui92/form-tailor) (institutional document formats) · [report-to-brief](https://github.com/parkjui92/report-to-brief) (report compression)

## License

[MIT](LICENSE). No proprietary institutional templates and no real client deliverables are included (bring-your-own-template principle).
