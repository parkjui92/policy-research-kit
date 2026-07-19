#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
geo_search.py — 지역·언어 현지화 웹검색 래퍼 (해외 자료 조사용)

미국 위치·영어 / 일본 위치·일본어 처럼 대상국 로케일(gl/hl/location)로
Google 검색을 수행한다. 프로바이더 무관: 아래 환경변수 중 설정된 것을 자동 사용.

  SERPER_API_KEY   https://serper.dev   (권장: 저렴, gl/hl/location 지원)
  SERPAPI_KEY      https://serpapi.com  (대안: 무료 100/월, 기능 풍부)

표준 라이브러리만 사용 → 별도 설치 불필요(python3만 있으면 됨).

사용 예:
  python3 geo_search.py -c jp "生成AI 規制 ガイドライン"
  python3 geo_search.py -c us "ARPA-H funding model" -n 10
  python3 geo_search.py --gl de --hl de --location "Germany" "Wasserstoff Foerderung"
  python3 geo_search.py --list-countries
  python3 geo_search.py -c jp --json "検索語"

핵심 원칙: **검색어는 대상국 언어로** 작성한다(미국=영어, 일본=일본어…).
이 스크립트는 '어디서(gl) / 어떤 언어 로케일(hl)로' 검색할지만 맞춘다.
"""
import argparse
import json
import os
import sys
import ssl
import urllib.request
import urllib.error
import urllib.parse

# macOS python.org 빌드 등에서 시스템 CA를 못 찾는 경우 대비: certifi 있으면 사용
try:
    import certifi
    _SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except Exception:
    _SSL_CTX = ssl.create_default_context()

# 국가 프리셋: gl(검색 위치) / hl(결과 언어 로케일) / location(도시·국가) / google_domain
PRESETS = {
    "us": {"gl": "us", "hl": "en",    "location": "United States", "google_domain": "google.com"},
    "jp": {"gl": "jp", "hl": "ja",    "location": "Japan",         "google_domain": "google.co.jp"},
    "kr": {"gl": "kr", "hl": "ko",    "location": "South Korea",   "google_domain": "google.co.kr"},
    "gb": {"gl": "gb", "hl": "en",    "location": "United Kingdom","google_domain": "google.co.uk"},
    "de": {"gl": "de", "hl": "de",    "location": "Germany",       "google_domain": "google.de"},
    "fr": {"gl": "fr", "hl": "fr",    "location": "France",        "google_domain": "google.fr"},
    "cn": {"gl": "cn", "hl": "zh-cn", "location": "China",         "google_domain": "google.com"},
    "tw": {"gl": "tw", "hl": "zh-tw", "location": "Taiwan",        "google_domain": "google.com.tw"},
    "sg": {"gl": "sg", "hl": "en",    "location": "Singapore",     "google_domain": "google.com.sg"},
}
ALIASES = {"uk": "gb", "usa": "us", "america": "us", "japan": "jp",
           "korea": "kr", "germany": "de", "france": "fr", "china": "cn", "taiwan": "tw"}

SETUP_HELP = """[geo_search] API 키가 설정되어 있지 않습니다.

지역 현지 검색(gl/hl)에는 SERP API 키가 필요합니다. 둘 중 하나를 준비하세요:

  1) Serper.dev (권장 · 저렴)   https://serper.dev  → 가입 후 API Key 복사
       export SERPER_API_KEY="발급받은키"
  2) SerpAPI (무료 100/월)      https://serpapi.com → API Key 복사
       export SERPAPI_KEY="발급받은키"

또는 키 파일에 저장(환경변수 대신): ~/.serper/key 또는 ~/.serpapi/key 에 키 한 줄.
셸 프로필(~/.zshrc)에 export 를 넣어두면 매번 자동 적용됩니다.
키 미설정 시에는 이 스크립트 대신 일반 WebSearch(영문 쿼리)로 폴백하세요.
"""


def resolve_locale(args):
    """프리셋 + 개별 오버라이드를 병합해 최종 로케일을 만든다."""
    loc = {"gl": "us", "hl": "en", "location": None, "google_domain": None}
    if args.country:
        key = args.country.strip().lower()
        key = ALIASES.get(key, key)
        if key not in PRESETS:
            sys.stderr.write(
                "[geo_search] 알 수 없는 국가 코드: %s\n  사용 가능: %s\n  (또는 --gl/--hl 로 직접 지정)\n"
                % (args.country, ", ".join(sorted(PRESETS))))
            sys.exit(2)
        loc.update(PRESETS[key])
    # 개별 오버라이드
    if args.gl:
        loc["gl"] = args.gl
    if args.hl:
        loc["hl"] = args.hl
    if args.location:
        loc["location"] = args.location
    if args.google_domain:
        loc["google_domain"] = args.google_domain
    return loc


def serper_search(key, q, loc, num):
    body = {"q": q, "gl": loc["gl"], "hl": loc["hl"], "num": num}
    if loc.get("location"):
        body["location"] = loc["location"]
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        "https://google.serper.dev/search", data=data,
        headers={"X-API-KEY": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as r:
        j = json.loads(r.read().decode("utf-8"))
    out = []
    for it in j.get("organic", []):
        out.append({"title": it.get("title", ""), "url": it.get("link", ""),
                    "snippet": it.get("snippet", ""), "date": it.get("date", "")})
    return out


def serpapi_search(key, q, loc, num):
    params = {"engine": "google", "q": q, "gl": loc["gl"], "hl": loc["hl"],
              "num": num, "api_key": key}
    if loc.get("location"):
        params["location"] = loc["location"]
    if loc.get("google_domain"):
        params["google_domain"] = loc["google_domain"]
    url = "https://serpapi.com/search.json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(urllib.request.Request(url), timeout=30, context=_SSL_CTX) as r:
        j = json.loads(r.read().decode("utf-8"))
    out = []
    for it in j.get("organic_results", []):
        out.append({"title": it.get("title", ""), "url": it.get("link", ""),
                    "snippet": it.get("snippet", ""), "date": it.get("date", "")})
    return out


def _read_keyfile(path):
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as f:
            v = f.read().strip()
        return v or None
    except Exception:
        return None


def pick_provider(explicit):
    # 우선순위: 환경변수 → 키 파일(~/.serper/key, ~/.serpapi/key)
    serper = os.environ.get("SERPER_API_KEY") or _read_keyfile("~/.serper/key")
    serpapi = os.environ.get("SERPAPI_KEY") or _read_keyfile("~/.serpapi/key")
    if explicit == "serper":
        return ("serper", serper)
    if explicit == "serpapi":
        return ("serpapi", serpapi)
    # auto
    if serper:
        return ("serper", serper)
    if serpapi:
        return ("serpapi", serpapi)
    return (None, None)


def main():
    p = argparse.ArgumentParser(
        description="지역·언어 현지화 웹검색(해외 자료 조사용). 검색어는 대상국 언어로 작성.")
    p.add_argument("query", nargs="?", help="검색어 (대상국 언어로)")
    p.add_argument("-c", "--country", help="국가 프리셋: " + ", ".join(sorted(PRESETS)))
    p.add_argument("--gl", help="검색 위치 코드 직접 지정 (예: jp, us, de)")
    p.add_argument("--hl", help="결과 언어 로케일 직접 지정 (예: ja, en, de)")
    p.add_argument("--location", help="location 문자열 (예: 'Tokyo, Japan')")
    p.add_argument("--google-domain", dest="google_domain", help="google 도메인 (SerpAPI용)")
    p.add_argument("-n", "--num", type=int, default=10, help="결과 개수 (기본 10)")
    p.add_argument("--provider", choices=["auto", "serper", "serpapi"], default="auto")
    p.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    p.add_argument("--list-countries", action="store_true", help="프리셋 목록 출력 후 종료")
    args = p.parse_args()

    if args.list_countries:
        print("사용 가능한 국가 프리셋 (코드 → gl/hl/location):")
        for k in sorted(PRESETS):
            v = PRESETS[k]
            print("  %-3s → gl=%-5s hl=%-6s %s" % (k, v["gl"], v["hl"], v["location"]))
        print("별칭:", ", ".join("%s=%s" % (a, t) for a, t in sorted(ALIASES.items())))
        print("임의 로케일은 --gl/--hl/--location 로 지정.")
        return

    if not args.query:
        p.error("검색어가 필요합니다. 예) geo_search.py -c jp \"検索語\"")

    loc = resolve_locale(args)  # 국가코드·인자 검증을 키 체크보다 먼저

    provider, key = pick_provider(args.provider)
    if not key:
        sys.stderr.write(SETUP_HELP)
        sys.exit(2)

    try:
        if provider == "serper":
            results = serper_search(key, args.query, loc, args.num)
        else:
            results = serpapi_search(key, args.query, loc, args.num)
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:300]
        except Exception:
            pass
        sys.stderr.write("[geo_search] %s HTTP %s: %s\n%s\n"
                         % (provider, e.code, e.reason, detail))
        sys.exit(1)
    except urllib.error.URLError as e:
        sys.stderr.write("[geo_search] 네트워크 오류: %s\n" % e.reason)
        sys.exit(1)

    if args.json:
        print(json.dumps({"locale": loc, "provider": provider,
                          "query": args.query, "results": results},
                         ensure_ascii=False, indent=2))
        return

    header = "# geo_search: gl=%s hl=%s location=%s (provider=%s) — %d건 · query: %s" % (
        loc["gl"], loc["hl"], loc.get("location") or "-", provider, len(results), args.query)
    print(header)
    if not results:
        print("(결과 없음 — 검색어·로케일을 확인하세요)")
        return
    for i, r in enumerate(results, 1):
        date = (" · %s" % r["date"]) if r.get("date") else ""
        print("\n%d. %s%s\n   %s\n   %s" % (i, r["title"], date, r["url"], r["snippet"]))


if __name__ == "__main__":
    main()
