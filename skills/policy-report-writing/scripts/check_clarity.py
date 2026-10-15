#!/usr/bin/env python3
"""check_clarity.py — 보고서·브리프 초안의 명료성 점검기 (표준 라이브러리만).

문장은 매끄러운데 처음 읽는 독자가 한 번에 요지를 잡지 못하게 만드는 신호를 찾는다.
글이 자기 얘기를 하는 문장(요구 대응 과시·장 안내·작업 흔적), 문장 끝 대시 뒤 해설 꼬리,
독자 밖 전문어·설명 없는 비유, 낫표 속 표어, 키워드만 늘어놓은 줄, 말 대신 기호.

판정이 아니라 후보 목록이다. 표 칸과 제목 줄은 보지 않는다. 따옴표 안 표현은 '쓴 것'이
아니라 '언급한 것'이라 세지 않는다. 독자에게 표준인 용어(델파이·SOP)는 사람이 판단한다.

    python3 check_clarity.py 04_report_draft.md            # 점검 리포트(표준 출력)
    python3 check_clarity.py 초안.md --report 점검.md       # 파일로 저장
    python3 check_clarity.py 초안.md --json
    python3 check_clarity.py 초안.md --gate 45             # 명료성 지수 45 이상이면 exit 1
    python3 check_clarity.py --selftest

유형 정의와 고치는 법은 ../references/clarity-rules.md.
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LEXICON = os.path.join(HERE, "clarity_ko.json")

SEV_MULT = {"warn": 1.0, "strong": 2.2}
SCORE_K = 30.0
MIN_CHARS_FOR_DENSITY = 300
READER_QUESTIONS = ("이 문서가 결국 말하는 것은 / 누가 무엇을 언제 / 근거가 되는 숫자는 / "
                    "그래서 무엇을 하라는가 / 무엇이 아직 확실하지 않은가")

FENCE_RX = re.compile(r"^\s*(```|~~~)")
HEADING_RX = re.compile(r"^\s{0,3}#{1,6}\s")
HR_RX = re.compile(r"^\s*(?:-{3,}|_{3,}|\*{3,})\s*$")
TABLE_RX = re.compile(r"^\s*\|")
SENT_SPLIT_RX = re.compile(r"(?<=[.!?？！…。])(?<!\d\.)\s+")  # 날짜 2026. 8. 28.는 자르지 않는다

MARK_RX = re.compile(r"^(\s*)([□■◯○●ㅇ◦▪•∙·\-–－*※]|\d{1,2}[.)]|[①-⑳]|[➊-➓]|\(\d{1,2}\)|[가-하][.)])\s*")
HEAD_RX = re.compile(r"^\s*(?:#{1,6}\s|제\s?\d+\s?[장절]|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|\d+(?:\.\d+)+\.?\s|\d+\.\s|\d+\)\s"
                     r"|[➊-➓]|\(\d+\)\s|[가-하]\.\s|<[^>]{2,40}>$|〈[^〉]{2,40}〉$)")
PRED_END_RX = re.compile(r"(?:함|임|음|됨|있음|없음|했음|였음|않음|한다|이다|된다|있다|없다|했다|였다|않다|니다|요"
                         r"|함\)|임\))[.。)]?\s*$")
LABEL_RX = re.compile(r"^(?:\([^()]{1,25}\)|〔[^〔〕]{1,25}〕|[^—:：]{1,25}\s?[—:：]\s)")
GUIDE_RX = re.compile(
    r"^(?:본\s?(?:장|절|문서|보고서|연구|과제)(?:에서는|는|은)|이\s?(?:장|절)에서는|여기서는|다음과\s같이|아래와\s같이)"
    r"[^.\n]{0,80}?(?:다룬다|다룸|살펴본다|살펴봄|살펴보|제시한다|제시함|정리한다|정리함|분석한다|분석함|검토한다|검토함"
    r"|판정함|구성된다|구성됨|기술한다|기술함)")
BACKGROUND_RX = re.compile(r"^(?:최근|오늘날|급변하는|[가-힣]+\s시대(?:를|에|의)\s|[가-힣]+의\s(?:등장|확산|발전|고도화)"
                           r"(?:으로|에\s따라|과\s함께))")
DASH_RX = re.compile(r"\s[—–]\s|[가-힣)]—|—[가-힣(]")
TAIL_PRE_RX = re.compile(r"(?:함|임|음|됨|있음|없음|했음|였음|한다|이다|된다|있다|없다|했다|였다|며|고|하여|해|로|으로"
                         r"|는|은|게|도록|하고|하며)\s*$")
TAIL_POST_RX = re.compile(r"^\s*(?:이는|즉|곧|다만|나아가|특히|이\s(?:때|점)|따라서|그래서|이를|이로써|이로\s인해|이것은)")
CIRCLED_REF_RX = re.compile(r"[ⓐ-ⓩ](?:안(?:은|는|이|을|를|의|과|와|으로)?|를|을|은|는|가|이|의|와|과|로|으로)"
                            r"(?=[\s,.)]|$)")
EQ_RX = re.compile(r"[가-힣)\]]\s?=\s?[가-힣(\[]")
GOV_NOUN_END_RX = re.compile(r"(?:마련|구축|개선|진단|강화|확대|추진|검토|분석|수립|운영|지원|도입|조성|정비|발굴|제시"
                             r"|평가|관리|구성|개발|확보|활용|연계|점검|보완|정립)\s*[.)]?\s*$")
QUOTED_RX = re.compile(r"'[^'\n]{1,60}'|\"[^\"\n]{1,80}\"|‘[^’\n]{1,60}’|“[^”\n]{1,80}”")
# 작업 흔적으로 세는 태그만(〔표 1〕 같은 캡션 괄호는 제외)
WORK_TAG_RX = re.compile(r"〔\s*(?:출처|확인|검증|구체화|색인|미확인|미대조|조사\s?반영|추정|2차|보정|서지|방어|메모|주\s?:)"
                         r"[^〔〕\n]{0,120}〕")


def load_lexicon(path=LEXICON):
    with open(path, encoding="utf-8") as f:
        ents = [e for e in json.load(f)["entries"] if e.get("cat") == "U"]
    for e in ents:
        e["_rx"] = re.compile(e["pattern"])
    return ents


def units_of(text):
    """서술문 단위 목록. 코드·표·제목 줄은 빼고, 제목 줄에서 절을 나눈다."""
    units, sec, prev_blank, in_fence = [], 0, True, False
    for i, ln in enumerate(text.split("\n")):
        if FENCE_RX.match(ln):
            in_fence = not in_fence
            prev_blank = True
            continue
        if in_fence or not ln.strip() or HR_RX.match(ln):
            prev_blank = True
            continue
        if TABLE_RX.match(ln):
            continue
        raw = ln.rstrip().replace("**", "").replace("__", "")
        m = MARK_RX.match(raw)
        marker = m.group(2) if m else ""
        body = raw[m.end():].strip() if m else raw.strip()
        if not body:
            continue
        if HEADING_RX.match(ln) or (len(body) <= 50 and not PRED_END_RX.search(body)
                                    and HEAD_RX.match(raw) and not body.endswith((",", "·"))):
            sec += 1
            prev_blank = True
            continue
        if marker:
            units.append({"text": body, "line": i + 1, "kind": "list", "sec": sec, "para_start": prev_blank})
            prev_blank = False
        else:
            for k, s in enumerate([x.strip() for x in SENT_SPLIT_RX.split(body) if len(x.strip()) > 1] or [body]):
                units.append({"text": s, "line": i + 1, "kind": "prose", "sec": sec,
                              "para_start": prev_blank and k == 0})
            prev_blank = True  # 서술 문단은 줄마다 문단으로 본다
    return units


def analyze(text, lexicon=None):
    lexicon = lexicon if lexicon is not None else load_lexicon()
    units = units_of(text)
    body_chars = sum(len(re.sub(r"\s", "", u["text"])) for u in units)
    per_1k = (lambda n: n * 1000.0 / body_chars) if body_chars else (lambda n: 0.0)
    n_tags = len(WORK_TAG_RX.findall(text))
    findings = []

    def add(fid, utype, sev, label, hint, hits, weight=2, factor=1.0, note=""):
        pts = weight * SEV_MULT[sev] * factor if sev in SEV_MULT else 0.0
        findings.append({"id": fid, "utype": utype, "severity": sev, "label": label, "hint": hint,
                         "count": len(hits) if isinstance(hits, list) else hits,
                         "lines": [u["line"] for u in hits[:5]] if isinstance(hits, list) else [],
                         "excerpt": (hits[0]["text"][:70] if isinstance(hits, list) and hits else ""),
                         "points": round(pts, 2), "note": note})

    def by_count(n, warn_at, strong_at):
        return "strong" if n >= strong_at else ("warn" if n >= warn_at else None)

    # 어휘 신호
    for ent in lexicon:
        keep_quotes = ent["utype"] == "U4c"  # 낫표 표어는 괄호 자체가 신호
        hits = [u for u in units for _ in ent["_rx"].finditer(u["text"] if keep_quotes else QUOTED_RX.sub(" ", u["text"]))]
        n = len(hits) + (n_tags if ent["id"] == "U2D-WORKTRACE" else 0)
        if not n:
            continue
        if ent.get("mode") == "d10k":
            if n < ent.get("min", 2) or body_chars < MIN_CHARS_FOR_DENSITY:
                continue
            d = per_1k(n) * 10
            sev = "strong" if d >= ent.get("strong", 4.0) else ("warn" if d >= ent.get("warn", 2.0) else None)
        else:
            sev = by_count(n, ent.get("warn_at", 1), ent.get("strong_at", 3))
        if not sev:
            continue
        info = ent.get("grade") == "info"
        note = ("〔…〕 작업 태그 %d개 포함" % n_tags) if (ent["id"] == "U2D-WORKTRACE" and n_tags) else ""
        add(ent["id"], ent["utype"], "info" if info else sev, ent["label"], ent.get("hint", ""),
            hits if hits else n, weight=0 if info else ent.get("weight", 2), factor=min(2.0, 0.8 + 0.2 * n), note=note)

    # U1a 절 첫머리가 안내·배경
    first, size = {}, {}
    for u in units:
        size[u["sec"]] = size.get(u["sec"], 0) + 1
        first.setdefault(u["sec"], u)
    opens = [u for s, u in first.items() if size[s] >= 2 and (GUIDE_RX.search(u["text"]) or BACKGROUND_RX.search(u["text"]))]
    if len(opens) >= 2:
        add("U1A-OPENING", "U1a", "info", "절 첫머리가 안내·배경(요지가 뒤로 밀림)",
            "절 첫 문장에 결론·요지를 두고, 안내 문장은 지운다", opens, weight=0)

    # U3a 해설 꼬리 — 문장 끝 대시 뒤 원리·의의 해설. 표제형 대시("(라벨) — 부제")는 남긴다
    tails = []
    for u in units:
        mt = DASH_RX.search(u["text"])
        if not mt:
            continue
        pre, post = u["text"][:mt.start()].strip(), u["text"][mt.end():].strip()
        if len(pre) <= 15:
            continue
        if len(pre) <= 25 and not TAIL_PRE_RX.search(pre) and not TAIL_POST_RX.search(post):
            continue
        if TAIL_PRE_RX.search(pre) or TAIL_POST_RX.search(post):
            tails.append(u)
    if tails:
        d = per_1k(len(tails))
        sev = "strong" if (len(tails) >= 6 and d >= 0.6) else ("warn" if (len(tails) >= 3 and d >= 0.25) else None)
        if sev:
            add("U3A-TAIL", "U3a", sev, "해설 꼬리(문장 끝 긴 대시 뒤 원리·의의 해설)",
                "대시 뒤 해설은 지운다. 필요한 정보면 독립 문장으로. 표제형 대시는 남긴다",
                tails, factor=min(2.0, d / 0.25))

    # U5b 말 대신 기호 — ⓑ안으로 다시 가리키기, 한 문장에 =·↔ 겹치기(구간 표기·수식은 제외)
    def sym(tx):
        if CIRCLED_REF_RX.search(tx):
            return True
        if re.search(r"\d|[+×÷/*#]", tx):
            return False
        return (tx.count("↔") + len(EQ_RX.findall(tx))) >= 2
    syms = [u for u in units if sym(u["text"])]
    sev = by_count(len(syms), 2, 5)
    if sev:
        add("U5B-SYMBOL", "U5b", sev, "말 대신 기호(ⓑ안·=·↔로 관계 압축)",
            "기호를 말로 푼다. 원문자 열거·흐름 화살표·표 칸은 해당 없음", syms)

    # U7a 키워드 나열 — 서술어 없는 가운뎃점 묶음 줄
    kws = []
    for u in units:
        if u["kind"] != "list":
            continue
        tx = LABEL_RX.sub("", u["text"]).strip()
        items = [x.strip() for x in re.split(r"\s?·\s?", tx)]
        if (len(tx) <= 40 and len(items) >= 4 and all(0 < len(x) <= 10 for x in items)
                and not re.search(r"[()（）\"“”]", tx) and not PRED_END_RX.search(tx) and not GOV_NOUN_END_RX.search(tx)):
            kws.append(u)
    sev = by_count(len(kws), 3, 6)
    if sev:
        add("U7A-KEYWORDS", "U7a", sev, "키워드 나열(서술어 없는 가운뎃점 묶음)",
            "서술어를 넣어 무엇을 어떻게 하는지 밝힌다. 표 칸·소제목은 해당 없음", kws)

    raw = sum(f["points"] for f in findings)
    score = round(100.0 * raw / (raw + SCORE_K)) if raw > 0 else 0
    groups = {f["utype"][:2] for f in findings if f["severity"] in SEV_MULT}
    bucket = "높음" if (score >= 45 and len(groups) >= 2) else ("주의" if score >= 20 else "낮음")
    findings.sort(key=lambda f: (f["utype"], -SEV_MULT.get(f["severity"], 0)))
    return {"score": score, "bucket": bucket, "body_chars": body_chars, "units": len(units),
            "findings": findings, "reader_questions": READER_QUESTIONS}


SEV_LABEL = {"strong": "강", "warn": "주의", "info": "정보"}


def render(r, path):
    L = ["# 명료성 점검 — %s" % os.path.basename(path), "",
         "- 명료성 지수: **%d/100 (%s)** · 본문 %s자 · 서술 단위 %d" % (r["score"], r["bucket"], format(r["body_chars"], ","), r["units"]),
         "- 후보 목록이지 판정이 아니다. 표 칸·제목 줄·따옴표 안 표현은 세지 않았다.", ""]
    if not r["findings"]:
        L.append("기계로 잡히는 신호 없음. 아래 다섯 물음은 여전히 사람·검토관이 본다.")
    else:
        L += ["| 등급 | 유형 | 신호 | 건수 | 줄 | 예 |", "|---|---|---|---|---|---|"]
        for f in r["findings"]:
            L.append("| %s | %s | %s | %d | %s | %s |" % (
                SEV_LABEL[f["severity"]], f["utype"], f["label"], f["count"],
                ", ".join(map(str, f["lines"])), f["excerpt"].replace("|", "∣")))
        L += ["", "고치는 법:"]
        for f in r["findings"]:
            L.append("- **%s** — %s%s" % (f["utype"], f["hint"], (" (%s)" % f["note"]) if f["note"] else ""))
    L += ["", "처음 읽는 독자 물음(절마다 한 번 읽고 답이 나오는가): " + r["reader_questions"]]
    return "\n".join(L) + "\n"


SELFTEST = [
    ("요구 대응 과시", "본 보고서는 발주처 요구를 빠짐없이 반영하였다. 과업지시서 항목에 1:1로 대응하였다. "
     "요구를 정확히 충족하도록 설계하였다. 평가 항목에 정조준하였다.\n" * 6, "U2A-COMPLY"),
    ("작업 흔적", "청년 고용률은 45.2%임 [검증]\n지원 예산은 3,200억 원임 〔출처 확인 필요〕\n", "U2D-WORKTRACE"),
    ("해설 꼬리", "\n".join(["지원 대상을 소득 하위 50%로 넓혔음 — 이는 사각지대를 줄이려는 조치임"] * 4)
     + "\n" + "가" * 400, "U3A-TAIL"),
    ("표제형 대시는 아님", "(추진 주체) — 고용노동부\n(재원) — 고용보험기금\n" + "나" * 400, None),
    ("키워드 나열", "- 시험·평가·실증·인증\n- 발굴·육성·확산·정착\n- 수집·정제·분석·환류\n", "U7A-KEYWORDS"),
    ("개조식 명사형은 아님", "- 수집·정제·분석 체계 구축\n- 발굴·육성·확산 지원\n- 시험·평가·인증 제도 정비\n", None),
    ("표 칸은 보지 않음", "| 시험·평가·실증·인증 | 빠짐없이 반영 |\n| 발굴·육성·확산·정착 | 1:1로 대응 |\n", None),
    ("따옴표 안은 언급", "'빠짐없이 반영'이나 '정조준' 같은 표현은 쓰지 않는다.\n", None),
    ("낫표 표어", "정부는 「데이터가 곧 경쟁력이다」라는 원칙을 세웠다.\n", "U4C-SLOGAN"),
]


def selftest():
    lex = load_lexicon()
    bad = 0
    for name, text, want in SELFTEST:
        ids = {f["id"] for f in analyze(text, lex)["findings"] if f["severity"] != "info"}
        ok = (want in ids) if want else not ids
        bad += not ok
        print("%s %s%s" % ("통과" if ok else "실패", name, "" if ok else " — 탐지: %s" % sorted(ids)))
    print("자체검사 %d/%d" % (len(SELFTEST) - bad, len(SELFTEST)))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description="보고서·브리프 초안 명료성 점검(후보 목록)")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--report", help="리포트를 이 파일에 저장")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", type=int, help="명료성 지수가 이 값 이상이면 exit 1")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.path:
        ap.error("파일 경로가 필요합니다")
    with open(a.path, encoding="utf-8") as f:
        r = analyze(f.read())
    out = json.dumps(r, ensure_ascii=False, indent=1) if a.json else render(r, a.path)
    if a.report:
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out)
        print("명료성 지수 %d/100 (%s) → %s" % (r["score"], r["bucket"], a.report))
    else:
        sys.stdout.write(out)
    return 1 if (a.gate is not None and r["score"] >= a.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
