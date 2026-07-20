# Changelog

## Unreleased

- **라이선스 Apache-2.0 → MIT.** 이 저장소의 내용은 프롬프트·마크다운 자산이라 Apache-2.0의 핵심 이점인 특허 실시권 조항에 실익이 없고, §4(b)의 "변경 사실 고지" 의무가 이 저장소의 의도된 사용(각자 분야·기관에 맞게 고쳐 쓰기)과 오히려 충돌한다. Claude Code 스킬·플러그인 생태계의 사실상 표준도 MIT다. MIT는 Apache-2.0보다 제약이 적으므로 기존 이용자의 권리는 축소되지 않는다.
- README를 국문·영문 2종으로 전면 개편 — 제작 배경과 활용 시나리오 보강 (`README.md` / `README.en.md`)

## v1.0.0 (2026-07-20)

- **표준 보고서 모드(50p급) 전 과정 예제 추가** — `examples/policy-standard-demo/`: 같은 주제(고령자 디지털 정보격차)의 8장·본문 65p급·표 11종·참고문헌 51건 완주 기록.
  - 게이트1이 [필수] 4건(RQ↔조사 불일치·병목 판정 기준 부재·연쇄 규칙 부재·수용성 근거 전무)을 적발 → 설계 v2 반영
  - 게이트2 표본 대조 40건 불일치 0건, 참고문헌 51건 유령·누락 0건, [미확보] 5건 한계 절에 정직 기재
  - hwpx 정량 검증: 표 69/69 행 전수 일치, 본문 왕복 유사도 1.000000, 약 65p
- 브리프 모드 예제(4쪽)와 같은 주제라 **두 산출 모드의 규모·게이트 강도 대비**를 한눈에 볼 수 있다.

## v0.9.0 (2026-07-20) — 공개 후보(Release Candidate)

- 통합 저장소(policy-research-kits)에서 **단독 저장소로 분리** — 이 저장소 하나로 마켓플레이스 등록·설치 가능.
- 전 과정 예제(examples/)·검증 게이트 방법론(docs/) 동봉.
- 공개판 조정: `model: inherit` 기본, 팀 API 부재 시 순차 Agent 폴백, BYO-template, geo-search 내장.

다른 킷: https://github.com/parkjui92/rnd-proposal-kit · https://github.com/parkjui92/socsci-paper-kit
