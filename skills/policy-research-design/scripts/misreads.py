#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""의도 오독 사례 기록기 (표준 라이브러리만, 추가 전용).

설계자가 요청을 잘못 읽어 사용자가 바로잡은 일을 한 건씩 쌓는다.
같은 실수를 사람 기억에 두지 않고 설계자가 다음에 읽는 파일에 남기기 위해서다.

적는 때:
  - 목차 승인에서 방향이 뒤집혔을 때
  - 분기 질문의 답이 기본 가정과 달랐을 때
  - 초안을 본 사용자가 "이게 아닌데"라고 했을 때

읽는 때: 설계자가 요청 원문을 읽은 직후. 같은 유형의 단서가 이번 요청에 있으면
〔추론〕의 단서로 쓴다(등급은 여전히 〔추론〕 — 지난번의 정정이 이번에도 맞는다는 보장은 없다).

같은 유형이 두 번 쌓이면 summary 가 '승격 후보'로 표시한다. 그때는 사례 파일에 두지 말고
설계 스킬 본문의 규칙으로 올린다.

파일 위치: 환경변수 INTENT_MISREADS → 없으면 ~/.claude/intent-misreads.md
(요청 원문이 들어가므로 저장소에 넣지 않는다.)

사용:
  misreads.py add --harness policy --type 분량 --task "재고용 확대 보고서" \\
      --request "…정책연구보고서 하나 만들어줘. 너무 길 필요는 없어." \\
      --read "표준 보고서 모드라 본문 50쪽으로 설계" \\
      --fix "20쪽이면 돼" --rule "'보고서'라 해도 '길 필요 없다'가 붙으면 20쪽 안팎을 기본 가정으로"
  misreads.py list [--harness policy] [--type 분량] [--last 5]
  misreads.py summary
  misreads.py --selftest
"""
import argparse
import datetime
import os
import re
import sys
import tempfile

TYPES = ("분량", "독자", "용도", "범위", "결정", "승부처", "기여", "연구유형", "용어", "기한", "전제", "입장", "기타")
HEAD = """# 의도 오독 사례 (추가 전용)

설계자가 요청을 잘못 읽어 사용자가 바로잡은 기록이다. 지우거나 고쳐 쓰지 않는다.
설계자는 요청 원문을 읽은 뒤 이 파일을 읽고, 같은 유형의 단서가 있으면 〔추론〕의 단서로만 쓴다.
같은 유형이 두 번 쌓이면 설계 스킬 본문의 규칙으로 올린다(`misreads.py summary`).
"""
ENTRY_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2}) · (\S+) · (\S+)(?: · (.*))?$", re.M)


def path_of(arg=None):
    return os.path.expanduser(arg or os.environ.get("INTENT_MISREADS") or "~/.claude/intent-misreads.md")


def one_line(s):
    return re.sub(r"\s+", " ", (s or "").strip())


def add(path, harness, typ, request, read, fix, rule, task="", date=None):
    date = date or datetime.date.today().isoformat()
    new = not os.path.exists(path)
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    title = f"## {date} · {harness} · {typ}" + (f" · {one_line(task)}" if task else "")
    body = [
        title,
        f"- 요청 원문: \"{one_line(request)}\"",
        f"- 설계자의 읽기: {one_line(read)}",
        f"- 사용자의 정정(원문): \"{one_line(fix)}\"",
        f"- 다음에 적용할 것: {one_line(rule)}",
        "",
    ]
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(HEAD + "\n")
        f.write("\n".join(body) + "\n")
    return title


def entries(path):
    if not os.path.exists(path):
        return []
    text = open(path, encoding="utf-8").read()
    marks = list(ENTRY_RE.finditer(text))
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        out.append({"date": m.group(1), "harness": m.group(2), "type": m.group(3),
                    "task": m.group(4) or "", "text": text[m.start():end].rstrip()})
    return out


def summary(path):
    es = entries(path)
    if not es:
        return "오독 사례 없음"
    counts = {}
    for e in es:
        counts.setdefault(e["type"], []).append(e)
    lines = [f"오독 사례 {len(es)}건 — {path}"]
    for typ, group in sorted(counts.items(), key=lambda kv: -len(kv[1])):
        mark = "  ← 승격 후보: 설계 스킬 본문의 규칙으로 올린다" if len(group) >= 2 else ""
        hs = ", ".join(sorted({g["harness"] for g in group}))
        lines.append(f"  {typ}: {len(group)}건 ({hs}){mark}")
    return "\n".join(lines)


def selftest():
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("  통과  " if cond else "  실패  ") + name)
        ok = ok and cond

    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.md")
        add(p, "policy", "분량", "보고서 하나 만들어줘.\n너무 길 필요는 없어.", "50쪽으로 설계", "20쪽이면 돼", "길 필요 없다 → 20쪽", "재고용", "2026-10-01")
        add(p, "paper", "분량", "학회보에 낼 논문", "학위논문 분량", "25,000자야", "학회보 → 기고요령 분량", "", "2026-10-02")
        add(p, "proposal", "승부처", "제안서 써줘", "인프라를 승부처로", "데이터가 핵심이야", "강조어를 먼저 본다", "", "2026-10-02")
        es = entries(p)
        expect("세 건이 쌓인다", len(es) == 3)
        expect("머리말은 한 번만", open(p, encoding="utf-8").read().count("# 의도 오독 사례") == 1)
        expect("줄바꿈이 한 줄로 정리된다", "만들어줘. 너무 길" in es[0]["text"])
        expect("과제명 없는 건도 읽힌다", es[1]["task"] == "" and es[1]["harness"] == "paper")
        s = summary(p)
        expect("같은 유형 2건이면 승격 후보", "분량: 2건" in s and "승격 후보" in s.split("분량: 2건")[1].split("\n")[0])
        expect("1건짜리는 승격 후보 아님", "승격 후보" not in s.split("승부처: 1건")[1])
        before = open(p, encoding="utf-8").read()
        add(p, "policy", "독자", "a", "b", "c", "d", "", "2026-10-03")
        expect("앞의 기록을 건드리지 않는다(추가 전용)", open(p, encoding="utf-8").read().startswith(before))
    print("자체 검사 " + ("전건 통과" if ok else "실패 있음"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="의도 오독 사례 기록기")
    ap.add_argument("--file", help="사례 파일 경로(기본 ~/.claude/intent-misreads.md)")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    a = sub.add_parser("add", help="사례 한 건 추가")
    a.add_argument("--harness", required=True, help="policy / proposal / paper / 그 밖의 이름")
    a.add_argument("--type", required=True, choices=TYPES, help="어긋난 유형")
    a.add_argument("--request", required=True, help="요청 원문(해당 구절)")
    a.add_argument("--read", required=True, help="설계자가 어떻게 읽었는가")
    a.add_argument("--fix", required=True, help="사용자가 바로잡은 말(원문)")
    a.add_argument("--rule", required=True, help="다음에 적용할 것(조건 → 읽는 법)")
    a.add_argument("--task", default="", help="과제명")
    a.add_argument("--date", help="일어난 날(YYYY-MM-DD). 지난 일을 뒤늦게 적을 때 쓴다. 기본은 오늘")
    ls = sub.add_parser("list", help="사례 보기")
    ls.add_argument("--harness")
    ls.add_argument("--type")
    ls.add_argument("--last", type=int)
    sub.add_parser("summary", help="유형별 건수와 승격 후보")
    sub.add_parser("path", help="사례 파일 경로")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    p = path_of(args.file)
    if args.cmd == "add":
        if args.date and not re.match(r"^\d{4}-\d{2}-\d{2}$", args.date):
            ap.error("--date 는 YYYY-MM-DD 형식")
        print("추가: " + add(p, args.harness, args.type, args.request, args.read, args.fix, args.rule, args.task, args.date))
        print(summary(p))
    elif args.cmd == "list":
        es = [e for e in entries(p)
              if (not args.harness or e["harness"] == args.harness) and (not args.type or e["type"] == args.type)]
        if args.last:
            es = es[-args.last:]
        print("\n\n".join(e["text"] for e in es) if es else "오독 사례 없음")
    elif args.cmd == "summary":
        print(summary(p))
    elif args.cmd == "path":
        print(p)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
