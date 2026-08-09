# 강점 한눈에 · 무엇을 연결하면 좋은가

이 킷을 남에게 소개하거나 도입을 검토할 때 쓰는 한 장이다. 각 항목의 상세 근거는 링크한 문서에 있다.

---

## 강점 7

### 1. 글을 쓴 AI가 자기 글을 검사하지 않는다

검수자(`policy-report-reviewer`)는 **읽기 전용(READ-ONLY)** 이다. 본문을 한 줄도 쓰지 않고, 고치지도 못하며, 지적만 한다. 집필자가 스스로를 통과시키는 이해충돌을 구조로 차단한 것이 이 킷의 뼈대다. → [점검 구조 상세](verification-gates.md)

### 2. 멈춰야 할 때 두 번 멈춘다

- **게이트 1 (집필 전)** — 목차·연구질문·분석틀이 실행 가능한지 GO/NO-GO 판정. 잘못된 목차로 50쪽을 써 버리면 되돌릴 수 없기 때문에, 쓰기 **전에** 검사한다.
- **게이트 2 (집필 후)** — 완성 원고를 5축(논리·근거·정책 타당성·정량성·교열 + 참고문헌 실재 검증)으로 검수한다.

동봉 예제 실측: 게이트 1이 [필수] 지적 4건(연구질문↔조사 불일치, 판정 기준 부재 등)을 집필 전에 적발해 설계를 고쳤다. → [`examples/`](../examples/)

### 3. 방향은 사람이 정한다

게이트 1 통과 직후 파이프라인이 멈추고 **목차 승인**을 요청한다. "3장을 해외사례 중심으로"라고 답하면 그 자리에서 재설계한다. 50쪽을 쓰기 전, 방향을 바꾸기에 가장 값싼 시점에 사람이 개입한다.

### 4. 출처는 열어보고 단다

일반 세션은 검색 결과 요약만으로 인용을 완성한다 — 원문 열람 0회. 이 킷은 핵심 수치의 원문을 실제로 열어 대조하고, 확인 못 한 것은 숨기지 않고 `[미확보]`로 표기한다.

실측 A/B(같은 주제·같은 모델, 제3자 감사): 수치·귀속 오류 **순정 2건 vs 킷 0건**. 표준 예제에서는 참고문헌 51건 중 유령 인용 0건, 표본 대조 40건 불일치 0건. → [비교 실험 전체 기록](vanilla-vs-kit.md)

### 5. 과정이 전부 파일로 남는다

`01_design.md`(목차 설계) → `02_design_gate.md`(1차 판정) → `03_evidence*.md`(근거장부) → `04_report_draft.md`(초안) → `05_draft_review.md`(2차 지적) → `06_report.hwpx`(최종). 몇 달 뒤 "이 숫자 어디서 나왔나"에 근거장부로 답할 수 있고, "3장만 다시"·"hwpx만 재생성" 같은 부분 재실행이 이 파일들을 기준으로 동작한다.

### 6. 늦어지면 스스로 가벼워진다 (v1.1.0)

역할에 맞는 모델 배치가 기본값이다 — 조사는 `sonnet`(검색·수집 중심), 변환은 `haiku`(기계적 절차), 설계·집필·검수는 세션 모델. 그 위에 "빨리 해줘" 한마디로 켜지는 쾌속 프로파일(조사 분할 병렬·집필 배치 분할), 지연을 감지하면 남은 단계를 순서대로 경량화하는 폴백 래더, 하위 모델이 자체 검증에 실패하면 상위 모델로 올리는 업시프트까지 네 겹이다. 단, **검수자는 어떤 경우에도 낮추지 않는다.** → [런타임 노트 §2](runtime-notes.md)

### 7. 한국 정책연구 실무의 출구로 끝난다

산출은 한글 `.hwpx`이고, 변환 후 정량 자체검증(표 행수 1:1 대조, 본문 왕복 유사도)을 통과해야 완료로 친다. 표준 예제 실측: 표 69/69행 전수 일치, 왕복 유사도 1.000000. 표준 보고서(50p+)와 정책브리프(4~8p) 두 크기를 같은 팀·같은 게이트로 낸다.

### 한계도 그대로

문장 자체는 일반 세션이 더 매끄럽다. 점검은 오류를 줄여줄 뿐 없애주지 못하며, 최종 확인은 사람 몫이다. 실측 비교는 1회 사례다. — 이 정직성 자체가 이 킷의 규율이다(모르면 `[미확보]`, 안 열어봤으면 안 열어봤다고 쓴다).

---

## 무엇을 연결하면 좋은가

이 킷은 특정 도구를 하드코딩하지 않는다. **세션에 연결된 도구와 키를 조사관·변환가가 그대로 쓴다.** 연결 방법은 두 가지뿐이다.

- **MCP형** — `claude mcp add ...`로 세션에 연결하면 서브에이전트도 사용한다.
- **키형 API** — 키를 발급받아 환경변수로 두고, 요청에 "통계는 ○○ 오픈API로 확인해줘"라고 한 줄 지시하면 조사관이 그 원천을 우선 사용한다.

### 공통 권장 2가지

| 연결 | 명령/설정 | 효과 |
|---|---|---|
| [kordoc](https://github.com/chrisryugj/kordoc) | `claude mcp add kordoc -- npx -y kordoc@latest mcp` | 한글 `.hwpx` 산출. 없으면 마크다운까지만 |
| SERP 키 (선택) | `SERPER_API_KEY`([serper.dev](https://serper.dev)) 또는 `SERPAPI_KEY`([serpapi.com](https://serpapi.com), 무료 100/월) | 내장 geo-search 활성 — 해외 사례를 대상국 언어·로케일로 검색(일본 사례는 일본어로). 키 없으면 기본 검색 폴백 |

### 연구 성격별 추천

| 이런 연구라면 | 이것을 연결·지정 | 왜 |
|---|---|---|
| 법·제도 분석이 큰 비중 | [국가법령정보 공동활용 API](https://open.law.go.kr) · [열린국회정보](https://open.assembly.go.kr) | 조문·개정 이력·계류 의안을 2차 기사가 아닌 1차 출처로 |
| 통계 중심 현황 진단 | [KOSIS 공유서비스](https://kosis.kr/openapi) · [공공데이터포털](https://www.data.go.kr) | "있는 숫자를 엉뚱한 지표에 붙이는" 오류([사례](why.md))는 통계 포털 원표 대조로만 차단된다 |
| 학술 선행연구 검증 | [KCI 오픈API](https://www.kci.go.kr) + 검색 원천으로 [NKIS](https://www.nkis.re.kr)·[PRISM](https://www.prism.go.kr) 지정 | 국내 학술·정책연구는 국제 DB에 없다 — 국내 원천 없이는 실재 검증이 "출처 불명"으로 끝난다 |
| 해외 사례 비교 | SERP 키(위) + 대상국 정부·국제기구 사이트 지정 | 미국 로케일 검색으로는 일본 후생노동성 원자료에 닿지 못한다 |
| 국제개발(ODA) | [OECD Data](https://data.oecd.org)(CRS) · [IATI Datastore](https://datastore.iatistandard.org) | 공여국 통계·사업 데이터의 표준 원천 |
| 지자체 연구 | [자치법규정보시스템](https://www.elis.go.kr) | 조례·규칙은 국가법령 DB와 별도 체계다 |

> 어느 것도 필수는 아니다. 아무것도 연결하지 않아도 기본 웹검색으로 완주하며, 연결할수록 근거장부의 1차 출처 비율이 올라간다.

---

## English TL;DR

Seven strengths: (1) the reviewer AI is read-only — the writer can never approve its own work; (2) two verification gates, one *before* drafting and one after; (3) a human approves the outline at the cheapest point to change direction; (4) sources are actually opened before citing — measured A/B: 2 factual errors (vanilla) vs 0 (kit), unverified figures marked `[unverified]` instead of asserted; (5) every stage persists as a file (design → gate ruling → evidence ledger → draft → review → final), enabling audits and partial re-runs; (6) v1.1.0 performance fallback: per-role model tiers, a fast profile, a delay ladder, and quality-upshift — the reviewer is never downgraded; (7) native Korean `.hwpx` output with quantitative self-verification. Optional integrations (kordoc MCP, SERP key for locale-aware search, Korean law/statistics/academic open APIs) raise the share of primary sources in the evidence ledger; none are required.
