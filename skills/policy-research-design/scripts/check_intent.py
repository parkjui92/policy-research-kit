#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""의도 확인서 결정론적 점검기 (표준 라이브러리만).

설계 문서의 의도 확인서가 요청 원문 원장과 맞는지를 기계로 확인한다.
판단이 필요한 것(과잉 해석·무게중심·질문의 질)은 검토관의 몫이고,
이 스크립트는 글자 대조로 답이 나오는 것만 본다.

  - 〔명시〕로 적은 인용이 원문에 글자 그대로 있는가 (리더 메모에만 있으면 등급 위조)
  - 요구어 대조표의 요구어가 원문에 있고, 반영 위치가 비어 있지 않은가
  - 원문 문장 가운데 요구어로 뽑히지 않은 것이 있는가
  - 설계 문서에 옮긴 요청 원문이 원장과 같은가
  - 분기 질문마다 기본 가정·"답이 다르면"이 달렸는가, 개수가 상한 안인가
  - 수용 기준이 있고, 판정하기 어려운 표현을 쓰지 않았는가
  - 확신도·의도 한 문장·「의도 대비 달라진 점」이 있는가

사용:
  check_intent.py --request _workspace/00_request.md --design _workspace/01_research_design.md
  check_intent.py --request ... --design ... --source _workspace/_decisions.md --source _workspace/00_input
  check_intent.py --selftest

종료 코드: 0 = [필수] 없음, 2 = [필수] 있음, 1 = 실행 오류.
"""
import argparse
import json
import os
import re
import sys
import unicodedata

GRADES = ("〔명시〕", "〔추론〕", "〔미상〕")
TAG_RE = re.compile(r"〔[^〕\n]{1,12}〕")
QUOTE_RE = re.compile(r'"([^"\n]{2,})"')
QUOTE1_RE = re.compile(r'"([^"\n]+)"')  # 요구어 대조표용 — "좀" 같은 한 글자 요구어도 인용으로 본다
ELLIPSIS_RE = re.compile(r"\s*(?:…+|\.{3,}|·{3,})\s*")
VAGUE = ("충분히", "적절히", "적절하게", "충실히", "충실하게", "효과적으로", "잘 드러", "분명하다", "명확하다", "명확히 드러")
KEY_ELEMENTS = ("용도", "독자", "결정", "기여", "역할", "범위")
EMPTY_CELL = {"", "—", "-", "–", "없음", "(없음)", "미상", "(미상)"}


def norm(text):
    """NFC, 따옴표 통일, 마크다운 강조 제거."""
    t = unicodedata.normalize("NFC", text)
    for a, b in (("“", '"'), ("”", '"'), ("„", '"'), ("‘", "'"), ("’", "'")):
        t = t.replace(a, b)
    return t.replace("**", "").replace("`", "")


def squash(text):
    """공백을 모두 지운 대조용 문자열."""
    return re.sub(r"\s+", "", norm(text))


def fragments(quote, minlen=2):
    """말줄임으로 이어 붙인 인용을 조각으로 나눈다."""
    out = []
    for part in ELLIPSIS_RE.split(quote):
        s = squash(part).strip(".,!?·:;")
        if len(s) >= minlen:
            out.append((part.strip(), s))
    return out


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


TEXT_EXT = (".md", ".txt")


def discover(request_path, given):
    """--source 가 없으면 원장 옆의 결정 원장과 00_input 을 자동으로 포함한다.
    글자로 읽지 못하는 첨부(hwpx·pdf 등)는 이름만 모아 돌려준다."""
    base = os.path.dirname(os.path.abspath(request_path))
    paths = list(given)
    if not paths:
        for name in ("_decisions.md", "00_input"):
            p = os.path.join(base, name)
            if os.path.exists(p):
                paths.append(p)
    unread = []
    for p in paths:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for root, _d, files in os.walk(p):
                for name in files:
                    if not name.startswith((".", "_")) and not name.lower().endswith(TEXT_EXT):
                        unread.append(name)
        elif os.path.isfile(p) and not p.lower().endswith(TEXT_EXT):
            unread.append(os.path.basename(p))
    return paths, sorted(unread)


def read_sources(paths):
    chunks = []
    for p in paths or []:
        p = os.path.expanduser(p)
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    if name.lower().endswith(TEXT_EXT):
                        try:
                            chunks.append(read(os.path.join(root, name)))
                        except (OSError, UnicodeDecodeError):
                            pass
        elif os.path.isfile(p) and p.lower().endswith(TEXT_EXT):
            chunks.append(read(p))
    return "\n".join(chunks)


def parse_ledger(text):
    """원장을 원문 구역과 리더 메모 구역으로 가른다."""
    lines = norm(text).splitlines()
    sections, cur_head, cur = [], "", []
    for ln in lines:
        if re.match(r"^#{1,4}\s", ln):
            sections.append((cur_head, cur))
            cur_head, cur = ln, []
        else:
            cur.append(ln)
    sections.append((cur_head, cur))
    orig, leader, first = [], [], []
    for head, body in sections:
        is_leader = "④" in head or "리더 메모" in head
        (leader if is_leader else orig).extend(body)
        if "①" in head or "최초 요청" in head:
            first.extend(b[1:].strip() for b in body if b.startswith(">"))
    if not first:  # 구역 표시가 없으면 첫 인용 블록을 최초 요청으로 본다
        for ln in lines:
            if ln.startswith(">"):
                first.append(ln[1:].strip())
            elif first:
                break
    return {
        "orig": "\n".join(orig),
        "leader": "\n".join(leader),
        "first": " ".join(x for x in first if x),
        "has_leader": bool(leader),
        "has_date": bool(re.search(r"접수[^\n]{0,12}\d{4}[-./]\s?\d{1,2}[-./]\s?\d{1,2}", "\n".join(lines))),
    }


def cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def is_sep(row):
    return bool(re.match(r"^\s*\|?\s*:?-{2,}", row))


class Report:
    def __init__(self):
        self.items = []

    def add(self, level, line, area, msg):
        self.items.append({"level": level, "line": line, "area": area, "msg": msg})

    def count(self, level):
        return sum(1 for i in self.items if i["level"] == level)


def check(request_text, design_text, source_text="", brief=False, unread=()):
    """unread: 글자로 읽지 못한 첨부(hwpx·pdf 등)의 파일명. 있으면 '원문에 없음'을 단정하지 않는다."""
    rep = Report()
    miss = "권고" if unread else "필수"
    miss_note = f" (읽지 못한 첨부 {len(unread)}건 — 사람이 대조)" if unread else ""
    led = parse_ledger(request_text)
    orig_sq = squash(led["orig"])
    leader_sq = squash(led["leader"])
    src_sq = squash(source_text)
    first_sq = squash(led["first"])
    lines = norm(design_text).splitlines()

    if not led["first"]:
        rep.add("필수", 0, "원장", "원장에서 최초 요청(① 인용 블록)을 찾지 못했다")
    if not led["has_date"]:
        rep.add("권고", 0, "원장", "원장 ①에 접수 일자가 없다 — 상대 시점(다음 달·내년)을 실제 날짜로 읽을 수 없다")
    if not led["has_leader"]:
        rep.add("참고", 0, "원장", "원장에 리더 메모(④) 구역이 없다 — 리더 해석이 원문과 섞였는지 확인")

    def locate(frag_sq):
        if frag_sq in orig_sq:
            return "orig"
        if src_sq and frag_sq in src_sq:
            return "source"
        if leader_sq and frag_sq in leader_sq:
            return "leader"
        return None

    # ---- 표 단위 순회 ------------------------------------------------------
    heading = ""
    table_kind, header = None, []
    req_frags = []          # 요구어 대조표에서 모은 조각
    unquoted_rows = []      # 따옴표 없는 요구어 행(빠진 것 등)
    filled_unknown = []     # 〔미상〕인데 내용 칸이 채워진 행
    has_req_table = False
    key_unknown = []        # 핵심 요소가 미상인 행
    for no, ln in enumerate(lines, 1):
        if re.match(r"^#{1,6}\s", ln):
            heading = ln
        if not ln.lstrip().startswith("|"):
            table_kind, header = None, []
            # 표 밖의 〔명시〕 인용은 참고로만 본다
            if "〔명시〕" in ln:
                for q in QUOTE_RE.findall(ln):
                    for raw, sq in fragments(q):
                        if locate(sq) is None:
                            rep.add("참고", no, "등급", f'〔명시〕 줄의 인용이 원문에 없다 — "{raw}"')
            continue
        if is_sep(ln):
            continue
        row = cells(ln)
        if table_kind is None:  # 표의 첫 행 = 머리
            header = row
            head_join = " ".join(row)
            if "요구어" in row[0] and "반영" in head_join:
                table_kind, has_req_table = "req", True
            elif any(c == "등급" for c in row):
                table_kind = "grade"
            else:
                table_kind = "other"
            continue

        if table_kind == "req":
            quotes = QUOTE1_RE.findall(row[0])
            joined = " ".join(row)
            inferred = "〔추론〕" in joined and "〔명시〕" not in joined  # 설계자가 추론이라 밝힌 행
            if not quotes:
                unquoted_rows.append(no)
            for q in quotes:
                for raw, sq in fragments(q, 1):
                    where = locate(sq)
                    if where == "orig" or where == "source":
                        req_frags.append(sq)
                    elif inferred:
                        continue
                    elif where is None:
                        rep.add("필수", no, "요구어 대조", f'원문에 없는 요구어 — "{raw}"')
                    else:
                        rep.add("필수", no, "요구어 대조", f'리더 메모에만 있는 말을 요구어로 올렸다 — "{raw}"')
            ti = next((i for i, h in enumerate(header) if "반영" in h), len(row) - 1)
            target = row[ti] if ti < len(row) else ""
            if target in EMPTY_CELL:
                rep.add("필수", no, "요구어 대조", f"반영 위치가 비어 있다 — {row[0][:40]}")
            continue

        if table_kind == "grade":
            joined = " ".join(row)
            tags = TAG_RE.findall(joined)
            grades = [t for t in tags if t in GRADES]
            try:
                gi = next(i for i, h in enumerate(header) if "등급" in h)
            except StopIteration:
                gi = None
            grade_cell = row[gi] if gi is not None and gi < len(row) else joined
            cell_tags = TAG_RE.findall(grade_cell)
            if not any(t in GRADES for t in cell_tags):
                if cell_tags:
                    rep.add("권고", no, "등급", f"등급 이름이 규격과 다르다 — {cell_tags[0]} (〔명시〕/〔추론〕/〔미상〕만 쓴다)")
                else:
                    rep.add("권고", no, "등급", f"등급이 없다 — {row[0][:30]}")
                continue
            main = next(t for t in cell_tags if t in GRADES)
            mixed = len(set(grades)) > 1
            if main == "〔명시〕":
                quotes = QUOTE_RE.findall(joined)
                if not quotes:
                    rep.add("권고", no, "등급", f"〔명시〕인데 원문 인용이 없다 — {row[0][:30]}")
                in_buyer = "발주처" in heading
                for q in quotes:
                    for raw, sq in fragments(q):
                        where = locate(sq)
                        if where in ("orig", "source"):
                            continue
                        if where == "leader":
                            rep.add("필수", no, "등급", f'리더 메모에만 있는 내용을 〔명시〕로 적었다 — "{raw}"')
                        elif in_buyer and not src_sq:
                            rep.add("참고", no, "등급", f'공고 인용 대조를 건너뜀(--source 미지정) — "{raw}"')
                        elif mixed:
                            rep.add("권고", no, "등급", f'〔명시〕 행의 인용이 원문에 없다(등급이 섞인 행) — "{raw}"')
                        else:
                            rep.add(miss, no, "등급", f'〔명시〕로 적은 인용이 원문에 없다 — "{raw}"{miss_note}')
            elif main == "〔추론〕":
                if len(row) >= 2 and row[-1] in EMPTY_CELL:
                    rep.add("권고", no, "등급", f"〔추론〕인데 단서가 없다 — {row[0][:30]}")
            elif main == "〔미상〕" and not mixed:
                if (len(row) >= 3 and gi != 1 and row[1] not in EMPTY_CELL
                        and not re.search(r"없음|미상|불명|모름|미정|미확|원문에|언급", row[1])):
                    filled_unknown.append(no)
                if any(k in row[0] for k in KEY_ELEMENTS):
                    key_unknown.append((no, row[0]))

    if filled_unknown:
        where = ", ".join(f"L{n}" for n in filled_unknown[:6])
        rep.add("참고", filled_unknown[0], "등급", f"〔미상〕인데 내용 칸이 채워진 행 {len(filled_unknown)}건({where}) — 그럴듯한 값을 넣은 것이 아닌지 확인")
    if unquoted_rows:
        rep.add("참고", unquoted_rows[0], "요구어 대조", f"따옴표 인용이 아닌 요구어 행 {len(unquoted_rows)}건 — 원문 대조를 건너뜀('빠진 것' 행이면 정상)")
    if not has_req_table:
        rep.add("필수", 0, "요구어 대조", "요구어 대조표가 없다(머리 행에 '요구어'와 '반영 위치'가 있어야 한다)")
    elif led["first"]:
        # 원문에서 어느 요구어로도 인용되지 않은 구간을 찾는다(띄어쓰기 차이는 무시)
        text = re.sub(r"\s+", " ", norm(led["first"])).strip()
        covered = [False] * len(text)
        for f in set(req_frags):
            pat = r"\s*".join(re.escape(ch) for ch in f)
            for mt in re.finditer(pat, text):
                for k in range(mt.start(), mt.end()):
                    covered[k] = True
        span = []
        for ch, cov in list(zip(text, covered)) + [("", True)]:
            if not cov:
                span.append(ch)
                continue
            piece = "".join(span).strip(" .,?!·")
            if len(re.sub(r"\s", "", piece)) >= 8:
                rep.add("권고", 0, "요구어 대조", f"요구어로 뽑히지 않은 원문 구간 — {piece}")
            span = []

    # ---- 요청 원문 인용 ----------------------------------------------------
    cands = []
    for i, ln in enumerate(lines):
        if "요청 원문" in ln and not ln.lstrip().startswith("|"):
            j = i + 1
            while j < len(lines) and j < i + 6 and not lines[j].startswith(">"):
                j += 1
            buf, start = [], j
            while j < len(lines) and lines[j].startswith(">"):
                buf.append(lines[j][1:].strip())
                j += 1
            if buf:
                cands.append((start + 1, squash(" ".join(buf))))
    if not cands:
        rep.add("권고", 0, "요청 원문", "의도 확인서에 요청 원문 인용 블록이 없다")
    elif first_sq and not any(q == first_sq or first_sq in q for _n, q in cands):
        rep.add("필수", cands[0][0], "요청 원문", "설계 문서에 옮긴 요청 원문이 원장 ①과 다르다(글자 그대로 옮기지 않음)")

    full = "\n".join(lines)

    # ---- 의도 한 문장 · 확신도 · 달라진 점 ----------------------------------
    if "의도 한 문장" not in full:
        rep.add("필수", 0, "의도 한 문장", "의도 한 문장이 없다")
    m = re.search(r"확신도[^\n]{0,24}?(높음|낮음)", full)
    if not m:
        rep.add("필수", 0, "확신도", "확신도(높음/낮음) 판정이 없다")
    elif m.group(1) == "높음" and key_unknown:
        names = ", ".join(n for _l, n in key_unknown)
        rep.add("권고", key_unknown[0][0], "확신도", f"핵심 요소가 〔미상〕인데 확신도가 '높음'이다 — {names}")
    if "의도 대비 달라진 점" not in full:
        rep.add("권고", 0, "의도 침식", "「의도 대비 달라진 점」 칸이 없다(없으면 '없음'이라 적는다)")

    # ---- 분기 질문 --------------------------------------------------------
    q_pat = re.compile(r"^\s*(?:[-*]\s*)?Q(\d+)[.)]\s*(.*)")
    q_starts = [(i, q_pat.match(ln)) for i, ln in enumerate(lines) if q_pat.match(ln)]
    seen, blocks = set(), []
    for idx, (i, mt) in enumerate(q_starts):
        num = int(mt.group(1))
        if num in seen:
            continue
        seen.add(num)
        end = len(lines)
        for i2, _m2 in q_starts[idx + 1:]:
            end = i2
            break
        j = i + 1
        while j < end and not re.match(r"^#{1,6}\s", lines[j]):
            j += 1
        blocks.append((i + 1, num, lines[i:j]))
    limit = 2 if brief else 3
    if not blocks:
        if "분기 질문 없음" not in full:
            rep.add("참고", 0, "분기 질문", "분기 질문이 없다 — 없으면 '분기 질문 없음'이라 적는다")
    else:
        if len(blocks) > limit:
            rep.add("권고", blocks[0][0], "분기 질문", f"분기 질문이 {len(blocks)}개다(상한 {limit}개) — 목차를 가장 크게 바꾸는 순으로 남긴다")
        for no, num, body in blocks:
            text = "\n".join(body)
            if "기본 가정" not in text:
                rep.add("필수", no, "분기 질문", f"Q{num}에 기본 가정이 없다 — 답이 없으면 진행할 수 없다")
            if "답이 다르면" not in text:
                rep.add("권고", no, "분기 질문", f'Q{num}에 "답이 다르면 바뀌는 곳"이 없다')
            stem = []
            for b in body:
                if "기본 가정" in b:
                    break
                stem.append(b)
            if "\n".join(stem).count("?") >= 2:
                rep.add("참고", no, "분기 질문", f"Q{num}에 물음이 둘 이상 묶여 있다 — 한 질문에 물음 하나")

    # ---- 수용 기준 --------------------------------------------------------
    # 가정 목록도 A1…으로 번호를 매기는 경우가 있어 '수용 기준' 제목 아래 구역에서만 센다
    a_pat = re.compile(r"^\s*(?:[-*|]\s*)?A(\d+)\s*[.)|:]\s*(.*)")
    crit = {}
    for i, ln in enumerate(lines):
        if "수용 기준" in ln and len(ln) < 70 and not ln.lstrip().startswith("|") and not a_pat.match(ln):
            j, found = i + 1, False
            while j < len(lines) and j < i + 40:
                if re.match(r"^#{1,6}\s", lines[j]) or "의도 대비 달라진 점" in lines[j]:
                    break
                mt = a_pat.match(lines[j])
                if mt:
                    found = True
                    crit.setdefault(int(mt.group(1)), (j + 1, mt.group(2)))
                j += 1
            if found:
                break
    lo, hi = (2, 3) if brief else (3, 5)
    if not crit:
        rep.add("필수", 0, "수용 기준", "수용 기준(A1 …)이 없다 — 초안을 판정할 기준이 없다")
    else:
        if not lo <= len(crit) <= hi + 1:
            rep.add("참고", min(v[0] for v in crit.values()), "수용 기준", f"수용 기준이 {len(crit)}개다(권장 {lo}~{hi}개)")
        for num, (no, body) in sorted(crit.items()):
            hit = [w for w in VAGUE if w in body]
            if hit:
                rep.add("권고", no, "수용 기준", f"A{num}에 판정하기 어려운 표현이 있다 — {', '.join(hit)} (예/아니오로 답할 수 있게)")

    info = {
        "분기 질문": len(blocks),
        "수용 기준": len(crit),
        "확인할 전제": "있음" if "확인할 전제" in full else "없음",
        "★ 가정": full.count("★"),
        "확신도": m.group(1) if m else "없음",
        "요구어": len(req_frags),
    }
    return rep, info


def render(rep, info, design_path=""):
    out = [f"의도 확인서 점검 — {design_path}".rstrip(" —")]
    out.append("  " + " · ".join(f"{k} {v}" for k, v in info.items()))
    order = {"필수": 0, "권고": 1, "참고": 2}
    for it in sorted(rep.items, key=lambda x: (order[x["level"]], x["line"])):
        loc = f"L{it['line']}" if it["line"] else "—"
        out.append(f"  [{it['level']}] {loc:>5} {it['area']}: {it['msg']}")
    out.append(f"판정: [필수] {rep.count('필수')} · [권고] {rep.count('권고')} · [참고] {rep.count('참고')}"
               + ("  → 게이트 전에 고친다" if rep.count("필수") else "  → 글자 대조 통과(해석의 타당성은 검토관이 본다)"))
    return "\n".join(out)


# ---- 자체 검사 --------------------------------------------------------------
_LEDGER = """# 요청 원문 원장
## ① 최초 요청 (사용자가 쓴 글자 그대로)
접수: 2026-10-01

> 도 차원에서 청년 농업인 정착 지원을 손보려고 합니다. 도의회 업무보고가 11월이라 그 전에 정책연구보고서로 정리해 주세요.

## ④ 리더 메모 (해석 — 원문 아님)
- 산출물 모드: 표준 보고서 모드로 판별
"""
_GOOD = """## 1. 의도 확인서
**요청 원문**
> 도 차원에서 청년 농업인 정착 지원을 손보려고 합니다. 도의회 업무보고가 11월이라 그 전에 정책연구보고서로 정리해 주세요.

**의도 한 문장** — 도 담당 과가 업무보고에서 개편 방향을 제시할 수 있어야 한다.
**확신도** — 낮음 (결정이 추론)

| 요소 | 내용 | 등급 | 인용 또는 단서 |
|---|---|---|---|
| 용도 | 도의회 업무보고 | 〔명시〕 | "도의회 업무보고가 11월이라" |
| 독자 | 도의원 | 〔추론〕 | 단서: 업무보고의 청중 |
| 성공 기준 | | 〔미상〕 | — |

| 원문의 요구어 | 성분 | 설계 반영 위치 |
|---|---|---|
| "도 차원에서 … 손보려고 합니다" | 동사 | RQ1 · 4장 |
| "도의회 업무보고가 11월이라" | 쓰임 | 요약 1쪽 |
| "정책연구보고서로 정리해 주세요" | 산출물 | 전체 |

**수용 기준**
- A1. 비교한 대안이 모두 도의 예산·조례로 실행할 수 있는 수단이다
- A2. 권고안에 소요 재원과 시행 시점이 적혀 있다
- A3. 맨 앞 한 쪽에 요약이 있다

**의도 대비 달라진 점** — 없음

## 2. 분기 질문
Q1. 개편안을 내는 연구입니까, 지적의 타당성부터 따지는 연구입니까?
  · 기본 가정: 개편안
  · 답이 다르면: 4장이 바뀐다
"""
_BAD = _GOOD.replace('"도의회 업무보고가 11월이라" |\n| 독자', '"기재부 예산 협의 전에" |\n| 독자') \
            .replace('| 〔명시〕 | "기재부', '| 〔명시〕 | "기재부', 1) \
            .replace("| 성공 기준 | | 〔미상〕 | — |", '| 분량 | 50쪽 | 〔명시〕 | "표준 보고서 모드로 판별" |') \
            .replace("RQ1 · 4장", "—") \
            .replace("  · 기본 가정: 개편안\n", "") \
            .replace("- A2. 권고안에 소요 재원과 시행 시점이 적혀 있다", "- A2. 대안을 충분히 비교한다")


def selftest():
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("  통과  " if cond else "  실패  ") + name)
        ok = ok and cond

    rep, info = check(_LEDGER, _GOOD)
    expect("정상 문서에 [필수] 0", rep.count("필수") == 0)
    expect("정상 문서 요구어 3개 인식", info["요구어"] >= 3)
    expect("말줄임 인용을 조각으로 대조", not any("손보려고" in i["msg"] for i in rep.items))
    rep, info = check(_LEDGER, _BAD)
    msgs = "\n".join(f"{i['level']}|{i['msg']}" for i in rep.items)
    expect("원문에 없는 〔명시〕 인용 적발", "필수|〔명시〕로 적은 인용이 원문에 없다" in msgs)
    expect("리더 메모를 〔명시〕로 올린 것 적발", "리더 메모에만 있는 내용을 〔명시〕로" in msgs)
    expect("반영 위치 공란 적발", "반영 위치가 비어 있다" in msgs)
    expect("기본 가정 없는 분기 질문 적발", "기본 가정이 없다" in msgs)
    expect("판정하기 어려운 수용 기준 적발", "판정하기 어려운 표현" in msgs)
    rep, _ = check(_LEDGER, _GOOD.replace("손보려고 합니다. 도의회", "개편하려고 합니다. 도의회", 1))
    expect("고쳐 옮긴 요청 원문 적발", any(i["area"] == "요청 원문" and i["level"] == "필수" for i in rep.items))
    rep, _ = check(_LEDGER, _GOOD.replace("| \"정책연구보고서로 정리해 주세요\" | 산출물 | 전체 |\n", ""))
    expect("요구어로 뽑히지 않은 원문 구간 적발", any("뽑히지 않은" in i["msg"] and "정책연구보고서" in i["msg"] for i in rep.items))
    led1 = _LEDGER.replace("정리해 주세요.", "좀 정리해 주세요.")
    good1 = _GOOD.replace("정리해 주세요.", "좀 정리해 주세요.").replace("| \"정책연구보고서로 정리해 주세요\" | 산출물 | 전체 |", "| \"정책연구보고서로\" | 산출물 | 전체 |\n| \"좀\" | 수식 | 가정 G1 |\n| \"정리해 주세요\" | 동사 | 전체 |")
    rep, info = check(led1, good1)
    expect("한 글자 요구어도 인용으로 인식", info["요구어"] >= 5 and not any("따옴표 인용이 아닌" in i["msg"] for i in rep.items))
    rep, _ = check(_LEDGER, _GOOD.replace("〔미상〕 | — |", "〔확인〕 | — |"))
    expect("등급 이름 표류 적발", any("규격과 다르다" in i["msg"] for i in rep.items))
    rep, _ = check(_LEDGER, _GOOD.replace("- A1.", "- B1.").replace("- A2.", "- B2.").replace("- A3.", "- B3."))
    expect("수용 기준 누락 적발", any(i["area"] == "수용 기준" and i["level"] == "필수" for i in rep.items))
    print("자체 검사 " + ("전건 통과" if ok else "실패 있음"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="의도 확인서 결정론적 점검")
    ap.add_argument("--request", help="요청 원문 원장(00_request.md)")
    ap.add_argument("--design", help="설계 문서(01_*.md)")
    ap.add_argument("--source", action="append", default=[], help="추가 원문(결정 원장·공고문·00_input 폴더). 여러 번 지정 가능. 생략하면 원장 옆의 _decisions.md 와 00_input 을 자동으로 본다")
    ap.add_argument("--brief", action="store_true", help="브리프 경량판 기준(질문 2개·수용 기준 2~3개)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.request or not a.design:
        ap.error("--request 와 --design 이 필요하다")
    try:
        srcs, unread = discover(a.request, a.source)
        rep, info = check(read(a.request), read(a.design), read_sources(srcs), a.brief, unread)
        if unread:
            info["읽지 못한 첨부"] = len(unread)
    except (OSError, UnicodeDecodeError) as e:
        print(f"실행 오류: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    if a.json:
        print(json.dumps({"info": info, "items": rep.items}, ensure_ascii=False, indent=1))
    else:
        print(render(rep, info, a.design))
    return 2 if rep.count("필수") else 0


if __name__ == "__main__":
    sys.exit(main())
