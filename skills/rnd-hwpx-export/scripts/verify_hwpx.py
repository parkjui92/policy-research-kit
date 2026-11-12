#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_hwpx.py — 원고(마크다운)와 변환 결과(.hwpx)를 대조하는 정량 검증기

변환가의 "검증 통과" 보고를 그대로 믿지 않기 위한 도구다. 리더(오케스트레이터)가
변환 직후 직접 실행하고, **종료 코드**로 통과·재변환·모델 업시프트를 정한다.

  0 = 통과    1 = 불합격(아래 검사 중 하나 이상 실패)    2 = 사용법·입출력 오류

검사 항목
  1. 패키지 무결성 — zip 손상 여부, mimetype(application/hwp+zip, 첫 엔트리·무압축),
     필수 엔트리(META-INF/container.xml, Contents/content.hpf, header.xml, section*.xml),
     XML 정형성
  2. 표 대조 — 원고의 표마다 (행 수, 열 수)가 같은 표가 hwpx에 같은 순서로 있는가.
     hwpx에만 있는 표(표지·제목 상자 등 장식 표)는 참고로만 적는다
  3. 본문 대조율 — 원고의 문단·표 칸 텍스트가 hwpx 본문에 들어 있는 비율(글자 기준).
     빠진 대목은 원고 줄 번호와 함께 나열한다. 통째로 사라진 대목이 하나라도 있으면 불합격
  4. 수치 보존 — 원고에 나온 숫자가 hwpx에 같은 횟수 이상 있는가. 긴 문서에서는 숫자 하나가
     바뀌어도 대조율이 기준을 넘기므로 따로 센다
  5. 잔재 — hwpx 본문에 남은 마크다운 기호(**, |---, 줄머리 #)
  6. 참고 — hwpx에 남아 있는 [보강 필요]·〔…〕 표시 목록(제출 전 사람이 볼 것)

표준 라이브러리만 사용 → 별도 설치 불필요.

사용 예
  python3 verify_hwpx.py _workspace/04b_for_hwpx.md _workspace/06_proposal.hwpx
  python3 verify_hwpx.py 원고.md 결과.hwpx --min-coverage 0.99 --json
  python3 verify_hwpx.py 원고.md 결과.hwpx --no-tables      # 지정 양식 채우기 경로
  python3 verify_hwpx.py --selftest

한계: 쪽수·글꼴·여백은 검사하지 못한다. 쪽수는 한글에서 열어야 확정된다.
      원고는 실제로 변환에 넣은 파일(전처리본이 있으면 그것)을 준다.
"""
import argparse
import collections
import json
import os
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

MIMETYPE = b"application/hwp+zip"
NS_P = "http://www.hancom.co.kr/hwpml/2011/paragraph"
P, T, TBL, TR, TC = ("{%s}%s" % (NS_P, n) for n in ("p", "t", "tbl", "tr", "tc"))
SECTION_RE = re.compile(r"^Contents/section\d+\.xml$")

# 줄머리에서 떼어내는 글머리 기호 — 변환기가 문단 서식으로 옮기면서 글자를 없애는 것들
LEAD_MARKS = "□■◇◆○●◯ㅇ◦•·∙‣▶▷※-–—*+"


# ───────────────────────── 정규화 ─────────────────────────

def norm(s):
    """대조용 정규화: 공백 전부 제거, 따옴표·물결 등 변환기가 바꾸는 글자 통일."""
    s = s.replace(" ", " ")
    for a, b in (("“", '"'), ("”", '"'), ("‘", "'"), ("’", "'"), ("～", "~"), ("〜", "~")):
        s = s.replace(a, b)
    return re.sub(r"\s+", "", s)


def strip_inline(s):
    """마크다운 인라인 문법을 걷어내고 화면에 보일 글자만 남긴다."""
    s = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", s)            # 그림
    s = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", s)        # 링크 → 글자만
    s = re.sub(r"<br\s*/?>", " ", s, flags=re.I)
    s = re.sub(r"</?(?:sub|sup|u|b|i|em|strong|span)[^>]*>", "", s, flags=re.I)
    s = s.replace("**", "").replace("~~", "").replace("`", "")
    s = re.sub(r"\*(\S(?:[^*\n]*\S)?)\*", r"\1", s)             # *기울임* — 닫는 * 뒤에 조사가 바로 붙는다
    s = s.replace("\\|", "|").replace("\\*", "*").replace("\\_", "_")
    return s.strip()


def strip_lead(s):
    """줄머리의 목록 표시·글머리 기호·번호를 떼어낸다."""
    prev = None
    while prev != s:
        prev = s
        s = s.lstrip()
        s = re.sub(r"^>+\s*", "", s)                      # 인용
        s = re.sub(r"^#{1,6}\s+", "", s)                  # 제목
        s = re.sub(r"^\d{1,3}[.)]\s+", "", s)             # 1. 2)
        s = re.sub(r"^\[[ xX]\]\s+", "", s)               # 체크박스
        if s and s[0] in LEAD_MARKS and (len(s) == 1 or s[1] in " \t" or s[0] in "□■◇◆○●◯ㅇ◦•·∙‣▶▷※"):
            s = s[1:]
    return s.strip()


# ───────────────────────── 마크다운 읽기 ─────────────────────────

def split_row(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|") and not line.endswith("\\|"):
        line = line[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)]


def is_sep(line):
    cells = split_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", c or "") for c in cells)


def parse_markdown(text):
    """(segments, tables) — segments: [(줄번호, 글자)], tables: [{line, rows, cols}]"""
    text = re.sub(r"<!--.*?-->", lambda m: "\n" * m.group(0).count("\n"), text, flags=re.S)
    lines = text.split("\n")
    segments, tables = [], []
    i, n = 0, len(lines)
    if lines and lines[0].strip() == "---":               # 머리말(front matter)
        for j in range(1, n):
            if lines[j].strip() == "---":
                i = j + 1
                break
    in_code = False
    while i < n:
        line = lines[i]
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            in_code = not in_code
            i += 1
            continue
        if in_code:
            if s:
                segments.append((i + 1, s))
            i += 1
            continue
        if not s or re.fullmatch(r"[-*_]{3,}", s):        # 빈 줄·가로줄
            i += 1
            continue
        if s.startswith("|") and i + 1 < n and lines[i + 1].strip().startswith("|") and is_sep(lines[i + 1]):
            start, rows = i, []
            while i < n and lines[i].strip().startswith("|"):
                if not is_sep(lines[i]):
                    rows.append(split_row(lines[i]))
                i += 1
            tables.append({"line": start + 1, "rows": len(rows), "cols": max(len(r) for r in rows)})
            for k, row in enumerate(rows):
                for cell in row:
                    c = strip_lead(strip_inline(cell))
                    if c:
                        segments.append((start + 1 + k, c))
            continue
        c = strip_lead(strip_inline(strip_lead(s)))
        if c:
            segments.append((i + 1, c))
        i += 1
    return segments, tables


# ───────────────────────── hwpx 읽기 ─────────────────────────

def _paragraphs(el, buf, out):
    """문단(hp:p)마다 글자를 이어 붙여 out에 넣는다. 한 문단 안의 글자 조각(hp:t)은 서식이
    바뀌는 자리에서 갈라지므로 구분 없이 붙이고, 표 칸 속 문단은 별도 문단으로 센다."""
    for child in el:
        if child.tag == P:
            mine = []
            _paragraphs(child, mine, out)
            out.append("".join(mine))
        elif child.tag == T:
            if buf is not None:
                buf.append("".join(child.itertext()))
        else:
            _paragraphs(child, buf, out)

def read_hwpx(path):
    """(problems, text, tables) — problems가 비어 있지 않으면 무결성 불합격."""
    problems, texts, tables = [], [], []
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        return ["zip으로 열 수 없음: %s" % e], "", []
    with z:
        bad = z.testzip()
        if bad:
            problems.append("손상된 엔트리: %s" % bad)
        infos = z.infolist()
        names = [i.filename for i in infos]
        if not infos or infos[0].filename != "mimetype":
            problems.append("mimetype이 첫 엔트리가 아님")
        if "mimetype" in names:
            if z.read("mimetype").strip() != MIMETYPE:
                problems.append("mimetype 내용이 application/hwp+zip이 아님")
            if z.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
                problems.append("mimetype이 압축돼 있음(무압축이어야 함)")
        else:
            problems.append("mimetype 엔트리 없음")
        for need in ("META-INF/container.xml", "Contents/content.hpf", "Contents/header.xml"):
            if need not in names:
                problems.append("필수 엔트리 없음: %s" % need)
        sections = sorted((x for x in names if SECTION_RE.match(x)),
                          key=lambda x: int(re.search(r"\d+", x.split("/")[-1]).group()))
        if not sections:
            problems.append("본문 섹션(Contents/section*.xml) 없음")
        for name in names:
            if not name.lower().endswith((".xml", ".hpf")):
                continue
            try:
                root = ET.fromstring(z.read(name))
            except ET.ParseError as e:
                problems.append("XML 오류 %s: %s" % (name, e))
                continue
            if name in sections:
                _paragraphs(root, None, texts)
                for el in root.iter():
                    if el.tag == TBL:
                        trs = [c for c in el if c.tag == TR]
                        cols = max((sum(1 for c in tr if c.tag == TC) for tr in trs), default=0)
                        tables.append({"rows": len(trs), "cols": cols})
    return problems, "\n".join(texts), tables


# ───────────────────────── 대조 ─────────────────────────

def match_tables(md_tables, hw_tables):
    """원고 표를 hwpx 표 목록에서 순서대로 찾는다. (못 찾은 원고 표, 장식 표 수)"""
    missing, j = [], 0
    for t in md_tables:
        k = j
        while k < len(hw_tables) and (hw_tables[k]["rows"], hw_tables[k]["cols"]) != (t["rows"], t["cols"]):
            k += 1
        if k == len(hw_tables):
            # 열 수는 병합 때문에 달라질 수 있다 — 행 수만 같은 표가 있으면 무엇이 다른지 알려준다
            near = next((h for h in hw_tables[j:] if h["rows"] == t["rows"]), None)
            missing.append(dict(t, near=near))
        else:
            j = k + 1
    return missing, len(hw_tables) - (len(md_tables) - len(missing))


def coverage(segments, hw_text):
    hay = norm(hw_text)
    total = hit = 0
    missing = []
    for line, seg in segments:
        key = norm(seg)
        if len(key) < 2:
            continue
        total += len(key)
        if key in hay:
            hit += len(key)
            continue
        # 통째로는 없을 때: 문장부호에서 끊은 조각 단위로 다시 찾는다
        parts = [p for p in (norm(x) for x in re.split(r"[.。!?;:,()\[\]〔〕「」『』“”\"'→·/]", seg)) if len(p) >= 6]
        got = sum(len(p) for p in parts if p in hay)
        got = min(got, len(key))
        hit += got
        missing.append({"line": line, "text": seg[:80], "found": round(got / len(key), 2)})
    return (hit / total if total else 1.0), total, missing


def digit_runs(text):
    return collections.Counter(re.findall(r"\d+", text))


def numbers(segments, hw_text):
    """원고의 숫자(연속한 숫자열)가 hwpx에 같은 횟수 이상 있는지 센다."""
    md = digit_runs("\n".join(seg for _, seg in segments))
    hw = digit_runs(hw_text)
    lost = {k: (c, hw.get(k, 0)) for k, c in md.items() if hw.get(k, 0) < c}
    return sum(md.values()), lost


def residue(hw_text):
    out = {}
    for label, pat in (("**", r"\*\*"), ("|---", r"\|\s*:?-{3,}"), ("줄머리 #", r"(?m)^#{1,6}\s"), ("```", r"```")):
        c = len(re.findall(pat, hw_text))
        if c:
            out[label] = c
    return out


def markers(hw_text):
    found = []
    for m in re.finditer(r"\[보강 필요[^\]]*\]|〔[^〕]{1,30}〕", hw_text):
        found.append(m.group(0))
    return found


def verify(md_path, hwpx_path, min_coverage=0.995, check_tables=True):
    with open(md_path, encoding="utf-8") as f:
        segments, md_tables = parse_markdown(f.read())
    problems, hw_text, hw_tables = read_hwpx(hwpx_path)
    result = {"markdown": md_path, "hwpx": hwpx_path, "integrity": {"ok": not problems, "problems": problems}}
    fails = []
    if problems:
        fails.append("무결성")
    if check_tables:
        missing, extra = match_tables(md_tables, hw_tables)
        result["tables"] = {"markdown": len(md_tables), "hwpx": len(hw_tables), "matched": len(md_tables) - len(missing),
                            "missing": missing, "hwpx_only": extra, "ok": not missing}
        if missing:
            fails.append("표")
    cov, total, miss = coverage(segments, hw_text)
    result["coverage"] = {"ratio": round(cov, 4), "min": min_coverage, "chars": total,
                          "missing": miss, "ok": cov >= min_coverage}
    gone = [m for m in miss if m["found"] == 0]
    result["coverage"]["gone"] = len(gone)
    if cov < min_coverage:
        fails.append("본문 대조율")
    elif gone:
        result["coverage"]["ok"] = False
        fails.append("누락 대목")
    n_total, lost = numbers(segments, hw_text)
    result["numbers"] = {"total": n_total, "lost": {k: {"markdown": a, "hwpx": b} for k, (a, b) in lost.items()}, "ok": not lost}
    if lost:
        fails.append("수치")
    res = residue(hw_text)
    result["residue"] = {"found": res, "ok": not res}
    if res:
        fails.append("마크다운 잔재")
    marks = markers(hw_text)
    result["markers"] = {"count": len(marks), "items": marks[:50]}
    result["hwpx_chars"] = len(norm(hw_text))
    result["fails"] = fails
    result["ok"] = not fails
    return result


def report(r):
    ok = lambda b: "통과" if b else "불합격"
    out = ["[%s] %s ← %s" % ("통과" if r["ok"] else "불합격", os.path.basename(r["hwpx"]), os.path.basename(r["markdown"]))]
    out.append("1. 무결성: %s" % ok(r["integrity"]["ok"]))
    out += ["   - " + p for p in r["integrity"]["problems"]]
    if "tables" in r:
        t = r["tables"]
        out.append("2. 표: %s — 원고 %d개 중 %d개 일치 (hwpx 표 %d개, 그중 원고에 없는 표 %d개)"
                   % (ok(t["ok"]), t["markdown"], t["matched"], t["hwpx"], t["hwpx_only"]))
        for m in t["missing"]:
            near = " ← 행 수만 같은 표 있음(%d열)" % m["near"]["cols"] if m.get("near") else ""
            out.append("   - 원고 %d행째 표(%d행×%d열)에 맞는 표가 hwpx에 없음%s" % (m["line"], m["rows"], m["cols"], near))
    else:
        out.append("2. 표: 건너뜀(--no-tables)")
    c = r["coverage"]
    out.append("3. 본문 대조율: %s — %.2f%% (기준 %.2f%%, 원고 %d자)%s" % (ok(c["ok"]), c["ratio"] * 100, c["min"] * 100, c["chars"],
               "" if not c.get("gone") else ", 통째로 없는 대목 %d건" % c["gone"]))
    for m in c["missing"][:20]:
        out.append("   - 원고 %d행 (%.0f%%만 발견): %s" % (m["line"], m["found"] * 100, m["text"]))
    if len(c["missing"]) > 20:
        out.append("   - … 외 %d건" % (len(c["missing"]) - 20))
    nb = r["numbers"]
    out.append("4. 수치 보존: %s — 원고의 숫자 %d개%s" % (ok(nb["ok"]), nb["total"],
               "" if nb["ok"] else ", hwpx에 모자란 것: " + ", ".join(
                   "%s(원고 %d회·hwpx %d회)" % (k, v["markdown"], v["hwpx"]) for k, v in list(nb["lost"].items())[:10])))
    out.append("5. 마크다운 잔재: %s%s" % (ok(r["residue"]["ok"]),
               "" if r["residue"]["ok"] else " — " + ", ".join("%s %d곳" % kv for kv in r["residue"]["found"].items())))
    out.append("6. 참고: hwpx 본문 %d자(공백 제외). 남은 표시 %d건%s. 쪽수는 한글에서 열어 확인할 것."
               % (r["hwpx_chars"], r["markers"]["count"],
                  "" if not r["markers"]["count"] else " — " + ", ".join(sorted(set(r["markers"]["items"]))[:8])))
    return "\n".join(out)


# ───────────────────────── 자체검사 ─────────────────────────

def _make_hwpx(path, paras, tables, mimetype=MIMETYPE, stored=True):
    """자체검사용 최소 hwpx. tables: [[[칸, …], …], …]"""
    body = ['<?xml version="1.0" encoding="UTF-8"?>',
            '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="%s">' % NS_P]
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;")
    for p in paras:
        body.append("<hp:p><hp:run><hp:t>%s</hp:t></hp:run></hp:p>" % esc(p))
    for t in tables:
        rows = "".join("<hp:tr>%s</hp:tr>" % "".join(
            "<hp:tc><hp:subList><hp:p><hp:run><hp:t>%s</hp:t></hp:run></hp:p></hp:subList></hp:tc>" % esc(c) for c in row)
            for row in t)
        body.append("<hp:p><hp:run><hp:tbl>%s</hp:tbl></hp:run></hp:p>" % rows)
    body.append("</hs:sec>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), mimetype,
                   compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
        z.writestr("META-INF/container.xml", "<container/>")
        z.writestr("Contents/content.hpf", "<package/>")
        z.writestr("Contents/header.xml", "<head/>")
        z.writestr("Contents/section0.xml", "\n".join(body))


def selftest():
    md = """# 제안서

## 1. 필요성
**(주장)** 플랫폼이 필요하다. 활용률은 대기업 66.5%, 중소기업 52.7%다([출처](https://example.com)).

- □ 과업 목표 — 통합 지원
- 둘째 항목 `코드`
- 의지가 아니라 *방법*의 부재가 병목이다

| 지표 | 현재 | 목표 |
|------|------|------|
| TRL | 4 | 7 |
| 정확도 | [보강 필요] | 90% |
| 단축률 |  | — |

<!-- 주석은 대조하지 않는다 -->
"""
    paras = ["제안서", "1. 필요성", "(주장) 플랫폼이 필요하다. 활용률은 대기업 66.5%, 중소기업 52.7%다(출처).",
             "과업 목표 — 통합 지원", "둘째 항목 코드", "의지가 아니라 방법의 부재가 병목이다"]
    table = [["지표", "현재", "목표"], ["TRL", "4", "7"], ["정확도", "[보강 필요]", "90%"], ["단축률", "", "—"]]
    deco = [["표지 상자"]]
    cases = []
    with tempfile.TemporaryDirectory() as d:
        mdp = os.path.join(d, "a.md")
        with open(mdp, "w", encoding="utf-8") as f:
            f.write(md)
        hp = os.path.join(d, "a.hwpx")

        def run(name, expect_ok, expect_fail=None, **kw):
            r = verify(mdp, hp, **kw)
            good = r["ok"] == expect_ok and (expect_fail is None or expect_fail in r["fails"])
            cases.append((name, good, r["fails"]))

        _make_hwpx(hp, paras, [deco, table]);                     run("정상 변환(장식 표 포함)", True)
        _make_hwpx(hp, paras, [deco, table[:2]]);                 run("표 행 소실", False, "표")
        _make_hwpx(hp, paras[:2] + paras[3:], [table]);           run("문단 누락", False, "본문 대조율")
        _make_hwpx(hp, paras + ["**굵게** 남음"], [table]);        run("마크다운 잔재", False, "마크다운 잔재")
        _make_hwpx(hp, [x.replace("66.5", "65.6") for x in paras], [table]);  run("수치 변조", False, "수치")
        _make_hwpx(hp, paras, [[r[:] for r in table[:2]] + [["정확도", "", "90%"]] + table[3:]])
        run("표 칸 하나 비움(대조율은 기준 이상일 수 있음)", False)
        _make_hwpx(hp, paras, [table], mimetype=b"text/plain");   run("mimetype 오류", False, "무결성")
        _make_hwpx(hp, paras, [table], stored=False);             run("mimetype 압축", False, "무결성")
        with open(hp, "wb") as f:
            f.write(b"not a zip");                                run("zip 아님", False, "무결성")
        _make_hwpx(hp, paras, []);                                run("--no-tables는 표를 보지 않음", False, "본문 대조율", check_tables=False)
        r = verify(mdp, hp, check_tables=False)
        cases.append(("--no-tables 결과에 표 항목 없음", "tables" not in r, r["fails"]))
        _make_hwpx(hp, paras, [table])
        r = verify(mdp, hp)
        cases.append(("남은 [보강 필요] 표시 집계", r["markers"]["count"] == 1, r["markers"]["items"]))
    bad = [c for c in cases if not c[1]]
    for name, good, info in cases:
        print("  %s %s%s" % ("✓" if good else "✗", name, "" if good else "  ← %s" % (info,)))
    print("자체검사 %d/%d 통과" % (len(cases) - len(bad), len(cases)))
    return 0 if not bad else 1


# ───────────────────────── 명령줄 ─────────────────────────

def main(argv=None):
    ap = argparse.ArgumentParser(description="원고(마크다운)와 hwpx 변환 결과를 대조한다. 종료 코드 0=통과, 1=불합격, 2=오류.")
    ap.add_argument("markdown", nargs="?", help="변환에 넣은 원고(.md)")
    ap.add_argument("hwpx", nargs="?", help="변환 결과(.hwpx)")
    ap.add_argument("--min-coverage", type=float, default=0.995, help="본문 대조율 하한(기본 0.995)")
    ap.add_argument("--no-tables", action="store_true", help="표 대조를 건너뛴다(지정 양식 채우기 경로)")
    ap.add_argument("--json", action="store_true", help="결과를 JSON으로 출력")
    ap.add_argument("--selftest", action="store_true", help="자체검사 실행")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.markdown or not a.hwpx:
        ap.print_usage(sys.stderr)
        return 2
    for p in (a.markdown, a.hwpx):
        if not os.path.isfile(p):
            print("파일 없음: %s" % p, file=sys.stderr)
            return 2
    try:
        r = verify(a.markdown, a.hwpx, a.min_coverage, not a.no_tables)
    except (OSError, UnicodeDecodeError) as e:
        print("읽기 실패: %s" % e, file=sys.stderr)
        return 2
    except Exception as e:                                # 검증기 자체의 결함을 "불합격"으로 오인하지 않게
        print("검증기 내부 오류(%s): %s" % (type(e).__name__, e), file=sys.stderr)
        return 2
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json else report(r))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
