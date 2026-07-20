# policy-research-kit

정책연구보고서를 끝까지 쓰는 **5인 에이전트 팀** 플러그인. 표준 보고서(본문 50p+)와 단형 정책브리프(4~8p) 두 모드를 지원하며, 최종 산출물은 한글 `.hwpx`.

## 파이프라인

```
연구설계(designer) → 설계검토 게이트(reviewer 모드1, GO/NO-GO)
  → ★목차 사용자 승인 → 근거조사(investigator, 출처 병기)
  → 집필(writer, 50p+/브리프) → 초안검수(reviewer 모드2, 5축)
  → 한글 변환(hwpx-exporter, 정량 검증 스위트)
```

- **게이트가 두 번**: 잘못된 목차로 진행되는 비싼 헛작업을 집필 전에 차단하고, 집필 후에는 논리·근거·정책타당성·정량성·**참고문헌 실재 검증**의 5축으로 검수한다.
- **실전 기록**: 완주 3회 + 200p 기존 보고서 검수·보완 1회. 검수 게이트가 환각 출처 3건·단위 환산 10배 오류를 적발한 이력이 있다.

## 구성

| 에이전트 | 역할 | 스킬 |
|---|---|---|
| policy-research-designer | 의도분석·RQ·분석틀·목차 설계 | policy-research-design |
| policy-report-reviewer | 설계 게이트(모드1) + 초안 검수(모드2) | policy-report-review |
| policy-research-investigator | 통계·문헌·국내외 사례 조사 | policy-research (+geo-search 내장) |
| policy-report-writer | 논증형 본문 집필·참고문헌 정리 | policy-report-writing |
| hwpx-exporter | `.hwpx` 변환·정량 자체검증 | rnd-hwpx-export |

오케스트레이터 스킬 `rnd-policy-research-orchestrator`가 전체를 조율한다. "정책연구보고서", "정책브리프", "이슈페이퍼" 등의 요청에 자동 반응한다.

## 설치·사용

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

```
"지역 소멸 대응 정책연구보고서를 작성해줘. 관련 메모와 통계 파일 첨부."
"이 주제로 4쪽짜리 정책브리프만 빠르게."
"목차에서 3장을 해외사례 중심으로 바꿔줘"   ← 목차 승인 게이트에서
```

## 요구사항·폴백

- `.hwpx` 변환은 kordoc MCP 필요(미설치 시 마크다운 산출까지 진행). 기존 `.hwp` 보고서를 입력하면 표·그림이 평탄화되므로 **원본 수정 가이드** 방식으로 대응한다.
- 팀 API가 없는 환경은 순차 Agent 호출로 동일 파이프라인 실행 — 오케스트레이터의 "공개판 실행 노트" 참조.

## 문서·예제 (이 저장소 동봉)

- [examples/](examples/) — 전 과정 산출물: 설계 → 게이트 판정 → 근거 → 초안 → 검수 → 최종 파일
- [docs/vanilla-vs-kit.md](docs/vanilla-vs-kit.md) — **순정 Claude Code와의 실측 A/B 감사** (같은 요청·같은 모델·URL 전수 검증)
- [docs/verification-gates.md](docs/verification-gates.md) — 2단계 검증 게이트 설계 방법론
- [docs/runtime-notes.md](docs/runtime-notes.md) — 팀 API 폴백·kordoc 설치·geo-search 키·모델 선택

## 시리즈

다른 킷: [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) · 단독 검증 스킬: [fact-verify](https://github.com/parkjui92/fact-verify) · [paper-proofread](https://github.com/parkjui92/paper-proofread) · [form-tailor](https://github.com/parkjui92/form-tailor) · [report-to-brief](https://github.com/parkjui92/report-to-brief)

## 라이선스

Apache-2.0. 독점 기관 양식·실제 과제 산출물은 포함하지 않는다(BYO-template 원칙).
