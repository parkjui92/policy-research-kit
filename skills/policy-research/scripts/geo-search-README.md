# geo-search — 지역·언어 현지화 웹검색 래퍼

해외 자료 조사를 **대상국 위치(gl) + 대상국 언어 로케일(hl)** 로 수행하는 얇은 래퍼.
"미국 위치에서 영어로 / 일본 위치에서 일본어로" 검색을 재현한다.
제안서·정책연구·논문 세 하네스의 조사 에이전트가 공용으로 사용한다.

## 왜 필요한가
Claude Code 기본 `WebSearch` 도구는 **US 고정**이고 위치 파라미터가 없다.
따라서 "일본 위치에서 검색"이 불가능하다. 이 래퍼는 SERP API의 `gl`/`hl`/`location`
파라미터로 그 위치·언어 로케일 검색을 대신 수행한다(실제 IP 프록시는 아니지만,
정책·학술·시장 조사에 필요한 '현지 검색 결과'의 대부분을 재현).

## 준비 (1회) — API 키
둘 중 하나를 발급받아 환경변수로 설정한다. **키 발급·결제는 사용자가 직접** 한다.

| 프로바이더 | 링크 | 특징 |
|---|---|---|
| **Serper.dev** (권장) | https://serper.dev | 저렴, gl/hl/location 지원, 가입 즉시 키 |
| SerpAPI | https://serpapi.com | 무료 100/월, 기능 풍부, 상대적 고가 |

```bash
# ~/.zshrc 에 추가 후 새 터미널 (둘 중 준비한 것만)
export SERPER_API_KEY="발급받은키"     # 권장
# export SERPAPI_KEY="발급받은키"      # 대안
```
또는 **키 파일**로 저장할 수도 있다(환경변수 대신, env가 우선): `~/.serper/key` 또는 `~/.serpapi/key` 에 키를 한 줄로 넣으면 래퍼가 자동으로 읽는다.

키가 없으면 스크립트는 안내만 출력하고 종료한다(기존 WebSearch 흐름은 무영향).

> ⚠️ 흔한 함정: **Serper 키와 SerpAPI 키는 서로 다르다.** SerpAPI 키를 `SERPER_API_KEY`(또는 `~/.serper/key`)에 넣으면 Serper가 403 Unauthorized로 거부한다. 키는 발급받은 서비스에 맞는 변수/파일에 넣을 것.

## 사용법
```bash
python3 scripts/geo_search.py -c jp "生成AI 規制 ガイドライン"
python3 scripts/geo_search.py -c us "ARPA-H funding model" -n 10
python3 scripts/geo_search.py --gl de --hl de --location "Germany" "Wasserstoff Foerderung"
python3 scripts/geo_search.py --list-countries
python3 scripts/geo_search.py -c jp --json "検索語"   # 기계 소비용
```

### 핵심 원칙
- **검색어는 대상국 언어로 작성한다.** 이 래퍼는 '위치·언어 로케일'만 맞춘다.
  한국어 쿼리로 해외 자료를 찾지 않는다(미국=영어, 일본=일본어, 독일=독일어…).
- 결과의 **현지 1차 출처**(정부·공식기관·현지 학술 DB·현지 언론)를 우선한다.
- 인용 시 **원어 제목 + 한국어 병기 + URL/출처**를 남긴다.

## 국가 프리셋
`us jp kr gb de fr cn tw sg` (별칭: uk=gb, usa=us, japan=jp …).
목록·매핑은 `--list-countries`. 그 외 로케일은 `--gl/--hl/--location` 으로 직접 지정.
프리셋 추가는 `geo_search.py` 의 `PRESETS` 딕셔너리에 한 줄 추가.

## 옵션
```
positional: query                 검색어(대상국 언어)
-c, --country   국가 프리셋
--gl / --hl / --location / --google-domain   개별 로케일 오버라이드
-n, --num       결과 개수(기본 10)
--provider      auto|serper|serpapi (기본 auto: 있는 키 자동 선택)
--json          JSON 출력
--list-countries 프리셋 목록
```
