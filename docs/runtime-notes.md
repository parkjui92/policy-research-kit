# 런타임 노트 — 실행 환경별 안내

## 1. 에이전트 팀 API와 순차 폴백

오케스트레이터 스킬은 에이전트 팀 API(`TeamCreate`/`TaskCreate`/팀 `SendMessage` — 실험 기능)를 1차 경로로 기술한다. **이 API가 없어도 킷은 동작한다**: 같은 파이프라인을 전경(foreground) `Agent` 호출의 순차 실행으로 수행하면 된다. Phase 순서와 산출물 파일 계약(`_workspace/01…06`)은 동일하며, 실제 운영에서 전 단계 전경 실행으로 완주가 검증됐다.

주의: 백그라운드로 재개된 서브에이전트는 파일 Write/Edit가 거부될 수 있다. **수정 루프(writer 개정)는 전경 실행**하거나, 검수 승인된 수정안을 리더(메인 세션)가 직접 반영한다.

## 2. 모델 선택

공개판 에이전트 정의는 `model: inherit`(세션 모델 상속)가 기본이다. 50p급 보고서·제안서처럼 품질이 우선이면 스폰 시 opus급 지정을 권장한다. 조사·변환 단계는 상속 모델로도 충분한 경우가 많다.

## 3. 한글(.hwpx) 경로 — kordoc

```
claude mcp add kordoc -- npx -y kordoc@latest mcp
```

- 지정 양식이 있으면 폼 채우기(`parse_form`→`fill_form`), 없으면 `generate_document` 표준 생성.
- kordoc 미설치·장애 시: 마크다운/docx 산출까지 진행하고 변환만 보류한다. MCP 게이트 장애 시 `npx -y kordoc@latest` 직접 구동 우회도 스킬에 문서화돼 있다.
- **기존 .hwp를 입력으로 줄 때의 한계**: .hwp→마크다운 추출은 표·그림을 평탄화한다. 기존 보고서의 검수·보완 작업은 "원본 수정 가이드" 산출 방식을 권장한다(추출본 재생성으로 원본을 대체하지 않는다).
- 독점 기관 양식은 이 저장소에 포함되지 않는다(BYO-template). 자기 기관 양식은 런타임에 `_workspace/00_input/`으로 제공하라.

## 4. 해외 조사 현지화 — geo-search (선택)

조사 스킬 3종(policy-research / rnd-research / paper-research)에는 SERP API 래퍼(`scripts/geo_search.py`)가 내장돼 있다. 기본 WebSearch가 US 로케일 고정인 한계를 보완해 "일본 사례는 일본어로, 독일 통계는 독일어로" 검색한다.

- 키 설정(둘 중 하나): `SERPER_API_KEY`(serper.dev, 권장) 또는 `SERPAPI_KEY`(serpapi.com, 무료 100/월). 환경변수 또는 `~/.serper/key` 파일.
- 키가 없으면 스킬이 자동으로 WebSearch 폴백을 쓴다 — 필수 아님.

## 5. 산출물 워크스페이스

모든 킷은 작업 디렉토리에 `_workspace/`를 만들어 단계 산출물(설계→게이트 판정→근거→초안→검수→최종)을 파일로 남긴다. 재실행·부분 수정("3장만 다시", "hwpx만 재생성")은 이 파일들을 기준으로 동작하므로 **`_workspace/`를 지우지 말 것**. 저장소에 커밋하지 않도록 `.gitignore`에 포함돼 있다.
