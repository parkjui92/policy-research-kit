# policy-research-kit

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)

**한국어** · [English](README.en.md)

정책연구보고서를 연구설계부터 한글 `.hwpx` 제출본까지 쓰는 **5인 에이전트 팀** [Claude Code](https://claude.com/claude-code) 플러그인.
문장력이 아니라 **검증이 기본값**인 것이 차이다 — 어느 수치가 확인됐고 어느 수치가 미확정인지를 산출물이 스스로 밝힌다.

<!-- 데모 GIF 자리 -->

## 왜 게이트인가

같은 요청·같은 모델로 순정과 비교하고, 제3의 중립 세션이 인용 URL 14건을 전수 열어 원문 대조했다.

| | 순정 | 킷 |
|---|---|---|
| 인용 URL 원문 열람 | **0회** | 핵심 수치 전건 |
| 수치·귀속 오류 | **2건** (전량 확정 어조) | **0건** (미확정은 `[보강 필요]`) |
| 과정 산출물 | 0/5 | **5/5** |

순정이 문장은 더 낫다. 문제는 그 초안의 오류 2건을 **잡을 장치도 기록도 없다**는 것이다.

→ [전체 감사 기록](docs/vanilla-vs-kit.md) · [왜 만들었나·상세 사용법](docs/why.md)

## 파이프라인

```
설계 → 🚦게이트1(설계검토) → ★목차 승인 → 조사 → 집필 → 🚦게이트2(5축 검수) → hwpx
```

게이트1은 **비용**을 막고(잘못된 목차로 50쪽 쓰기 전에), 게이트2는 **과신**을 막는다.
검수자는 집필자와 **다른 에이전트**이고 읽기 전용이라, 자기 글을 자기가 통과시킬 수 없다.

실제 적발: 환각 출처 3건 · 단위 환산 10배 오류 · 모집단 오독 · 근거상 불가능한 RQ 하향.

## 설치

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

## 쓰는 법

```
지역 소멸 대응 정책연구보고서 써줘. 메모랑 통계 첨부했어    ← 표준 50p+
이 주제로 4쪽짜리 정책브리프만 빠르게                       ← 브리프 모드
이 200쪽 보고서 검수하고 근거 약한 곳 보완해줘              ← 기존 보고서 검수
3장을 해외사례 중심으로 바꿔줘                              ← 목차 승인 게이트에서
```

두 번 멈춰 선다(게이트1 후 목차 승인, 게이트2 후 수정 확인). 그사이 자리를 비워도 된다.

## 무엇이 남는가

문서 하나가 아니라 **감사 가능한 기록 한 벌** — 설계·게이트 판정·근거장부·검수 지적·수정 내역·최종 hwpx.
6개월 뒤 "이 수치 어디서 나왔냐"는 질문에 답할 수 있다는 뜻이다.

동봉 예제: [표준 65p급](examples/policy-standard-demo/) · [브리프](examples/policy-brief-demo/) · [순정 비교본](examples/vanilla-baseline/)

## 요구사항·한계

- `.hwpx` 변환에 [kordoc](https://github.com/chrisryugj/kordoc) MCP 필요 (없으면 마크다운까지 진행)
- **게이트는 오류를 줄이지 없애지 못한다.** 검수자도 같은 계열 모델이라 맹점을 공유할 수 있다
- A/B는 단일 실행·단일 주제다. 통계적 주장이 아니라 재현 가능한 사례다
- 국내 정책연구 관행(hwpx·국문 근거)에 맞춰져 있다
- [폴백·의존성·키 설정](docs/runtime-notes.md) · [게이트 설계 방법론](docs/verification-gates.md)

## 시리즈

**에이전트 팀 킷** — [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) (정부 R&D 제안서) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) (사회과학 논문)

**제작·편집 킷** — [lecture-deck-kit](https://github.com/parkjui92/lecture-deck-kit) (강의자료 HTML 덱 · 브라우저 라이브 편집)

**단독 스킬** — [fact-verify](https://github.com/parkjui92/fact-verify) (출처 검증) · [paper-proofread](https://github.com/parkjui92/paper-proofread) (한국어 학술 교정교열) · [form-tailor](https://github.com/parkjui92/form-tailor) (기관 양식 맞춤) · [report-to-brief](https://github.com/parkjui92/report-to-brief) (보고서 압축)

## 라이선스

[MIT](LICENSE). 독점 기관 양식·실제 수탁 산출물 미포함(BYO-template).
