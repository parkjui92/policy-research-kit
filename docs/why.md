# 왜 만들었나 · 상세 사용법

**한국어** · [English](#english)

README에서 덜어낸 배경과 사용 시나리오를 여기 둔다.

---

## 왜 만들었나

정책연구를 하면서 LLM에게 보고서 초안을 맡겨 본 사람은 대개 같은 경험을 한다. **결과물은 매끄럽다.** 문장이 좋고, 구성도 그럴듯하고, 말미에는 진짜로 존재하는 URL이 열 개쯤 달려 있다. 그래서 검증된 문서처럼 보인다.

문제는 그다음이다. 인용된 URL을 하나씩 실제로 열어보면 이런 것들이 나온다.

- **지표 혼동** — "AI 서비스 경험률 일반 국민 67.8% 대 고령층 32.1%". 67.8%라는 숫자 자체는 실재한다. 다만 전혀 다른 지표(65세 이상 디지털정보화 수준, 2023)의 값이다. 없는 숫자를 지어낸 것이 아니라 **있는 숫자를 엉뚱한 지표에 붙인 것**이라, 오히려 검산이 어렵다.
- **문서 귀속 오류** — 근거로 달린 연구보고서를 237쪽 전문까지 파싱해도 그 수치는 없다. 실제 출처는 다른 기관의 다른 조사였다.
- 그리고 두 오류 모두 **확정 어조**로 서술돼 있다. 읽는 사람이 걸러낼 단서가 문서 안에 없다.

이건 모델이 부족해서 생기는 문제가 아니다. **인용을 10건 달면서 원문은 0회 열어보는 공정**이 만드는 문제다. 검색 결과 요약만으로 인용이 완성되기 때문에, 틀려도 틀린 자리에 아무 표시가 남지 않는다.

정책연구에서 이건 특히 치명적이다. 보고서에 실린 수치는 다시 인용되고, 예산 근거가 되고, 몇 년 뒤 국정감사에서 다시 읽힌다. "AI가 그렇게 써 줬다"는 해명이 통하지 않는 종류의 문서다.

그래서 필요했던 것은 더 좋은 문장이 아니라 **공정(工程)**이었다.

1. 잘못된 목차로 50쪽을 쓰기 전에 멈추는 장치
2. 집필 후 근거를 원문과 대조하는 장치
3. 확인하지 못한 수치를 **확인하지 못했다고 표시하는** 규율

이 킷은 실제 정책연구 과제를 수행하면서 그 장치들을 하나씩 붙여 만든 결과물이다. 개인 작업용 하네스로 쓰던 것을 플러그인으로 정리해 공개한다.

한 가지 더 있다. 한국에서 정책연구를 하면 해외 도구가 넘지 못하는 벽이 둘이다. **제출 형식이 한글(`.hwpx`)**이라는 것, 그리고 **핵심 근거가 KCI·NKIS·국책연구원 보고서**에 있어서 국제 DB만으로는 "출처 불명" 처리된다는 것. 이 킷은 그 두 지점을 정면으로 다룬다.

---

## 순정 대비 실측 A/B — 전체 표

**같은 요청·같은 기반 모델**로 순정 세션과 이 킷을 각각 돌리고, **제3의 중립 감사 세션이 양쪽의 인용 URL 14건을 전수로 열어** 원문과 대조했다(237쪽 PDF 전문 파싱 포함).

| 항목 | A — 순정 | B — 킷 |
|---|---|---|
| 출처 부착률 | 60% (말미 목록 매핑 인정 시 87%) | **100% (전 주장 인라인)** |
| 인용 URL 원문 열람 | **0회** — 검색 요약만으로 인용 | 핵심 수치 전건 확인 후 인용 |
| **수치·귀속 오류** | **2건 + 연도 혼입 1건** | **0건** |
| 오류의 어조 | 전량 확정 어조 — 걸러낼 단서 없음 | 미확정 수치는 `[보강 필요]` 5곳으로 명시 강등 |
| 과정 산출물 | 0/5 — 본문 `.md` 1개 | **5/5** — 설계·게이트·근거장부·검수가 파일로 잔존 |
| 최종 형식 | `.md` | **`.hwpx`** |
| 문장·구성 품질 | **우위** — 완성도·맥락 폭·최신성 | 골격은 명료하나 분량·구체성 부족 |

**결론은 "순정이 못 쓴다"가 아니다.** 순정은 더 매끄러운 초안을 준다. 문장력만 놓고 보면 순정이 이겼고, 초고령사회 진입 시점 같은 최신 맥락도 순정이 더 정확했다. 문제는 그 초안 속 오류 2건을 **아무도 잡지 않았고, 잡을 장치도 기록도 없다**는 것이다.

전체 감사 기록은 [vanilla-vs-kit.md](vanilla-vs-kit.md)에 있다.

---

## 상세 사용법

### 시나리오 1 — 백지에서 표준 보고서 (본문 50p+)

```
지역 소멸 대응 정책연구보고서를 작성해줘.
관련 메모와 통계 파일 첨부했어.
```

설계 → 게이트1 → **목차 승인 요청** → 조사 → 집필 → 게이트2 → hwpx 순으로 진행된다.

### 시나리오 2 — 단형 정책브리프 (4~8p)

```
이 주제로 4쪽짜리 정책브리프만 빠르게.
```

같은 팀·같은 게이트를 쓰되 분량·목차(배경→쟁점→근거→제언)·검수 축이 경량 모드로 전환된다. 자문 회신, R&D Brief류에 쓴다.

### 시나리오 3 — 이미 있는 보고서를 검수·보완

```
이 200쪽 보고서 검수하고 근거 약한 곳 보완해줘.
```

⚠️ **기존 `.hwp`를 입력할 때 주의.** `.hwp`에서 텍스트를 추출하면 표·그림이 평탄화된다(원본 표 85개가 추출본에서 4개로 줄어든 사례가 있다). 그래서 이 킷은 추출본으로 새 파일을 만들어 원본을 대체하지 않고, **원본에 반영할 수정 가이드**를 1차 산출물로 준다. 검수자가 "도표 공란"을 오탐할 수 있다는 점도 함께 알린다.

### ★ 목차 승인 게이트에서 개입하는 법

파이프라인이 멈추고 목차를 보여줄 때가 **가장 값싸게 방향을 바꿀 수 있는 지점**이다.

```
3장을 해외사례 중심으로 바꿔줘
5장이 너무 크다 — 대안 비교랑 우선순위를 분리해줘
진단 대상을 4개 영역 말고 8대 분야로 재구성해줘
```

마지막은 실제로 있었던 재구성이고, 설계자가 되돌아가 8분야 체계로 다시 짰다.

### 조사 결과가 미덥지 않을 때

```
2장 근거가 약해. 해외 통계 더 찾아줘
이 수치 출처 다시 확인해줘
```

조사관은 모든 사실에 출처를 병기하도록 설계돼 있어, 어떤 문장의 근거가 무엇인지 근거장부(`03_evidence*.md`)에서 역추적할 수 있다.

---

## 팀 구성

| 에이전트 | 역할 | 스킬 |
|---|---|---|
| `policy-research-designer` | 의도분석·RQ·분석틀·목차 설계 | `policy-research-design` |
| `policy-report-reviewer` | 설계 게이트(모드1) + 초안 검수(모드2) · **READ-ONLY** | `policy-report-review` |
| `policy-research-investigator` | 통계·문헌·국내외 사례 조사 | `policy-research` (+geo-search 내장) |
| `policy-report-writer` | 논증형 본문 집필·참고문헌 정리 | `policy-report-writing` |
| `hwpx-exporter` | `.hwpx` 변환·정량 자체검증 | `rnd-hwpx-export` |

> **geo-search 내장.** 해외 사례를 조사할 때 기본 웹검색은 미국 로케일에 고정된다. 내장 래퍼는 대상국 언어·지역으로 검색해(일본 사례는 일본어로) 현지 1차 자료에 닿게 한다. 키가 없으면 기본 검색으로 자동 폴백한다.

산출 파일: `01_design.md` · `02_design_gate.md` · `03_evidence*.md` · `04_report_draft.md` · `05_draft_review.md` · `05b_fix_log.md` · `06_report.hwpx`

---
---

<a name="english"></a>

# Why I built this · Detailed usage

[한국어](#왜-만들었나--상세-사용법) · **English**

Background and usage scenarios trimmed out of the README.

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

## The measured A/B — full table

The **same request, the same underlying model**, run once through a vanilla session and once through this kit. Then a **neutral third-party audit session opened all 14 cited URLs from both outputs** and checked every figure against the source (including parsing that 237-page PDF in full).

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

The full audit is in [vanilla-vs-kit.md](vanilla-vs-kit.md).

---

## Detailed usage

### Scenario 1 — Standard report from scratch (50+ pages)

```
Write a policy research report on responses to regional depopulation.
Notes and statistics files attached.
```

Runs design → gate 1 → **outline approval** → research → drafting → gate 2 → hwpx.

### Scenario 2 — Short policy brief (4–8 pages)

```
Just a quick 4-page policy brief on this topic.
```

Same team, same gates, but length, outline (background → issues → evidence → recommendations) and review axes switch to a lightweight mode.

### Scenario 3 — Review and strengthen an existing report

```
Review this 200-page report and shore up the weakly-sourced parts.
```

⚠️ **A caveat when feeding in an existing `.hwp`.** Text extraction from `.hwp` flattens tables and figures — in one case an original with 85 tables came back with 4. So this kit does *not* regenerate a replacement file from the extraction. It produces a **revision guide to apply to your original** as the primary deliverable, and warns you that the reviewer may raise false positives about "empty tables."

### ★ Intervening at the outline approval gate

When the pipeline stops and shows you the outline, that is **the cheapest point at which to change direction**.

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

The investigator attaches a source to every fact, so you can trace any sentence back through the evidence ledger (`03_evidence*.md`).

---

## The team

| Agent | Role | Skill |
|---|---|---|
| `policy-research-designer` | Intent analysis, RQ, framework, outline | `policy-research-design` |
| `policy-report-reviewer` | Design gate (mode 1) + draft review (mode 2) · **READ-ONLY** | `policy-report-review` |
| `policy-research-investigator` | Statistics, literature, domestic/international cases | `policy-research` (+ built-in geo-search) |
| `policy-report-writer` | Argument-driven body, reference list | `policy-report-writing` |
| `hwpx-exporter` | `.hwpx` conversion with quantitative self-verification | `rnd-hwpx-export` |

> **Built-in geo-search.** Default web search is pinned to a US locale. The bundled wrapper searches in the target country's language and region (Japanese sources in Japanese), which is what it takes to reach local primary material. Without an API key it falls back to standard search.

Output files: `01_design.md` · `02_design_gate.md` · `03_evidence*.md` · `04_report_draft.md` · `05_draft_review.md` · `05b_fix_log.md` · `06_report.hwpx`
