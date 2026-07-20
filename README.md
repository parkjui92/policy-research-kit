# policy-research-kit

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](CHANGELOG.md)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
![Claude Code](https://img.shields.io/badge/Claude_Code-Plugin-purple.svg)

**한국어** · [English](README.en.md)

정책연구보고서를 처음부터 끝까지 대신 써 주는 [Claude Code](https://claude.com/claude-code) 플러그인입니다.

주제를 알려주시면 목차를 짜고, 근거 자료를 찾고, 본문을 쓰고, 한글 파일(`.hwpx`)로 만들어 드립니다. 역할이 다른 다섯 개의 AI가 나눠 맡는데, 그중 하나는 **검사만 하는 역할**입니다. 글을 쓴 AI가 자기 글을 스스로 통과시킬 수 없게 만든 것이 이 플러그인의 핵심입니다.

## 무엇이 다른가요

AI에게 보고서를 맡기면 결과물은 꽤 매끄럽게 나옵니다. 문제는 그 안에 적힌 숫자가 맞는지 **아무도 확인하지 않는다**는 점입니다. 진짜 있는 링크가 열 개쯤 달려 있으니 검증된 문서처럼 보이지만, 실제로 열어보면 다른 조사의 숫자를 가져다 붙인 경우가 나옵니다.

그래서 직접 재봤습니다. 같은 주제를 일반 Claude Code와 이 플러그인에 각각 맡기고, 제3자가 양쪽이 인용한 링크 14개를 **전부 열어서** 원문과 대조했습니다.

| | 일반 Claude Code | 이 플러그인 |
|---|---|---|
| 인용한 자료를 실제로 열어봤나 | 한 번도 안 열어봄 | 중요한 숫자는 전부 확인 |
| 숫자·출처가 틀린 것 | **2건** (모두 단정하는 말투) | **0건** (확인 못 한 건 `[보강 필요]`로 표시) |
| 작업 과정이 파일로 남았나 | 안 남음 | 5개 파일로 남음 |

솔직히 말씀드리면 **문장은 일반 Claude Code가 더 잘 씁니다.** 다만 그렇게 나온 초안에 틀린 숫자가 두 개 섞여 있었고, 그걸 걸러낼 방법도 나중에 되짚어볼 기록도 없었습니다.

→ [비교 실험 전체 기록](docs/vanilla-vs-kit.md) · [왜 만들었는지, 더 자세한 사용법](docs/why.md)

## 어떤 순서로 진행되나요

```
목차 설계 → 🚦1차 점검 → ★목차 확인 요청 → 자료 조사 → 본문 집필 → 🚦2차 점검 → 한글 파일
```

중간에 **두 번 멈춰 섭니다.** 첫 번째는 목차가 잘못되지 않았는지 보는 자리입니다. 목차가 어긋난 채로 50쪽을 써 버리면 되돌릴 방법이 없기 때문에, 쓰기 전에 확인합니다. 두 번째는 다 쓴 원고를 검사하는 자리입니다. 완성된 글은 그럴듯해 보여서 스스로 의심하기 어렵기 때문에, **글을 쓰지 않은 다른 AI**가 읽기 전용으로 검사합니다.

실제로 이 점검에서 걸린 것들입니다. 존재하지 않는 출처 3건, 단위를 10배로 잘못 환산한 숫자, 전체 평균을 특정 집단의 값처럼 써 놓은 부분, 그리고 근거가 부족한데 너무 세게 잡은 연구 질문입니다.

## 설치

```
/plugin marketplace add parkjui92/policy-research-kit
/plugin install policy-research-kit@policy-research-kit
```

## 이렇게 쓰시면 됩니다

평소 말하듯 요청하시면 됩니다.

```
지역 소멸 대응 정책연구보고서 써줘. 메모랑 통계 첨부했어      ← 본문 50쪽 이상
이 주제로 4쪽짜리 정책브리프만 빠르게                        ← 짧은 요약 보고서
이 200쪽 보고서 검수하고 근거 약한 곳 보완해줘               ← 이미 있는 보고서 손보기
3장을 해외사례 중심으로 바꿔줘                               ← 목차 확인 단계에서
```

마지막 줄처럼, 목차를 보여드릴 때 고쳐 달라고 하시면 그 자리에서 다시 짭니다. **방향을 바꾸기에 가장 값싼 시점**입니다.

## 무엇이 남나요

완성된 보고서 하나만 나오는 게 아니라, **작업 과정이 전부 파일로 남습니다.**

목차 설계안, 1차 점검에서 무엇을 왜 지적했는지, 어떤 사실을 어디서 가져왔는지 정리한 목록, 본문 초안, 2차 점검 지적과 실제로 고친 내역, 그리고 최종 한글 파일입니다.

몇 달 뒤에 "이 숫자 어디서 나온 거냐"는 질문을 받았을 때 답할 수 있다는 뜻입니다.

## 알아두실 점

- 한글 파일(`.hwpx`)로 만들려면 [kordoc](https://github.com/chrisryugj/kordoc)이라는 변환 도구가 따로 필요합니다. 없어도 마크다운까지는 정상적으로 나옵니다.
- **점검이 오류를 줄여주긴 하지만 없애주지는 못합니다.** 검사하는 AI도 같은 계열이라 비슷한 착각을 할 수 있습니다. 최종 확인은 사람이 해야 합니다.
- 위 비교 실험은 **한 주제를 한 번 돌려본 것**입니다. 통계적으로 증명된 수치가 아니라, 직접 재현해 보실 수 있는 사례로 봐주세요.
- 국내 정책연구 관행(한글 파일 제출, 국문 자료 중심)에 맞춰져 있습니다.
- [설치·설정에서 막힐 때](docs/runtime-notes.md) · [이런 점검 구조를 직접 만들고 싶다면](docs/verification-gates.md)

## 함께 만든 것들

**보고서·제안서를 써 주는 플러그인** — [rnd-proposal-kit](https://github.com/parkjui92/rnd-proposal-kit) (정부 R&D 제안서) · [socsci-paper-kit](https://github.com/parkjui92/socsci-paper-kit) (사회과학 논문)

**만들고 고치는 플러그인** — [lecture-deck-kit](https://github.com/parkjui92/lecture-deck-kit) (강의자료 HTML 덱 · 브라우저에서 바로 수정)

**하나씩 쓰는 도구** — [fact-verify](https://github.com/parkjui92/fact-verify) (출처가 진짜인지 확인) · [paper-proofread](https://github.com/parkjui92/paper-proofread) (한국어 논문 교정) · [form-tailor](https://github.com/parkjui92/form-tailor) (기관 양식에 맞춰 문서 작성) · [report-to-brief](https://github.com/parkjui92/report-to-brief) (긴 보고서를 짧게)

## 라이선스

[MIT](LICENSE). 특정 기관의 양식이나 실제 수행한 과제 결과물은 들어 있지 않습니다.
