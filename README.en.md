# policy-research-kit

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)

[한국어](README.md) · **English**

A [Claude Code](https://claude.com/claude-code) plugin that writes a policy research report for you, start to finish.

Give it a topic and it drafts an outline, gathers sources, writes the body, and produces a Korean `.hwpx` file (the document format Korean government offices require). Five AIs split the work, and one of them **only reviews** — so the AI that wrote the text can never sign off on its own work. That's the whole idea.

## What makes it different

Ask any AI to draft a research report and the writing comes out smooth. The catch is that **nobody checks whether the numbers in it are right.** Ten real, working links at the bottom make it look verified — but open them and you find figures borrowed from a different survey entirely.

So I measured it. I gave the same topic to plain Claude Code and to this plugin, then had a neutral third party **open all 14 cited links** from both and compare them against the originals.

| | Plain Claude Code | This plugin |
|---|---|---|
| Did it actually open its sources? | Never opened one | Opened every key figure |
| Wrong numbers or wrong attribution | **2** (all stated as fact) | **0** (unconfirmed ones marked "needs checking") |
| Did the work leave a trail? | No | 5 files |

To be straight with you: **plain Claude Code writes better prose.** The problem was that its draft had two wrong numbers in it, with no way to catch them and no record to check later.

→ [Full comparison](docs/vanilla-vs-kit.md) · [Why I built this, and fuller usage notes](docs/why.md)

## How it runs

```
Outline → 🚦Check 1 → ★You confirm the outline → Research → Writing → 🚦Check 2 → Korean file
```

It **stops twice.** The first stop catches a bad outline — once 50 pages exist against the wrong structure, there's no cheap way back, so it checks before writing. The second stop reviews the finished draft, because polished writing is hard to doubt on your own. That review is done by **a different AI that didn't write anything**, in read-only mode.

Things these checks have actually caught: 3 sources that didn't exist, a figure converted 10× off, an overall average written as if it applied to one specific group, and a research question claiming more than the evidence could support.

## Install

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

## Using it

Just ask in plain language.

```
Write a policy report on regional depopulation. Notes attached.   ← 50+ pages
Just a quick 4-page policy brief on this.                         ← short version
Review this 200-page report and shore up the weak sourcing.       ← fixing an existing one
Make chapter 3 center on international cases                      ← at the outline step
```

That last one matters: when it shows you the outline, asking for changes rebuilds it right there. **It's the cheapest moment to change direction.**

## What you end up with

Not just a finished report — **the whole process stays on disk as files.**

The outline, what the first check flagged and why, a list of which fact came from which source, the draft, what the second check found and what was actually changed, and the final Korean file.

Which means that months later, when someone asks where a number came from, you can answer.

## Good to know

- Producing the Korean `.hwpx` file needs a separate converter called [kordoc](https://github.com/chrisryugj/kordoc). Without it everything still runs and you get Markdown.
- **The checks reduce errors but don't eliminate them.** The reviewing AI comes from the same model family and can share the same blind spots. A person still needs to look.
- The comparison above was **one topic, run once**. Treat it as a case you can reproduce, not a proven statistic.
- It's shaped around Korean policy-research practice (HWPX submissions, Korean-language sources).
- [If setup gives you trouble](docs/runtime-notes.md) · [Building this kind of review structure yourself](docs/verification-gates.md)

## Related work

**Plugins that write reports and proposals** — [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) (Korean government R&D proposals) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) (social science papers)

**Plugins that build and edit** — [lecture-deck-kit](https://github.com/parkjui92/lecture-deck-kit) (HTML lecture slides you edit right in the browser)

**Single-purpose tools** — [fact-verify](https://github.com/parkjui92/fact-verify) (check whether sources are real) · [paper-proofread](https://github.com/parkjui92/paper-proofread) (Korean academic proofreading) · [form-tailor](https://github.com/parkjui92/form-tailor) (match an organization's document format) · [report-to-brief](https://github.com/parkjui92/report-to-brief) (shorten long reports)

## License

[MIT](LICENSE). Contains no organization-specific templates and no real client deliverables.
