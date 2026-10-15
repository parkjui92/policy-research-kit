#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""설계자 회귀 세트 실행기 (표준 라이브러리만).

설계 스킬을 고칠 때마다 같은 요청들로 설계자를 다시 돌려, 의도 읽기가 나빠지지 않았는지 본다.
에이전트를 띄우는 일은 리더가 하고, 이 스크립트는 앞뒤를 맡는다.

  1) prepare — 사례의 요청 원장·첨부를 실행 폴더에 펴고, 사례별 스폰 프롬프트를 만든다
  2) (리더가 spawn_prompts.md 의 프롬프트로 설계자를 사례마다 띄운다. 병렬 가능)
  3) score   — 산출물마다 check_intent 글자 대조 + 사례별 기대 항목을 채점한다

사례는 regression/cases/<id>/ 에 둔다.
  00_request.md   요청 원문 원장
  00_input/       첨부(있으면)
  case.json       {"id", "harness": policy|paper|proposal, "origin", "brief", "note",
                   "expect": [{"id", "desc", "where", "any"|"all"|"none": [정규식…]}],
                   "judge": ["사람·검토관이 볼 것 …"]}
"expect" 는 기계가 채점하고, "judge" 는 채점표에 그대로 찍어 사람이 본다.
"where" 를 주면 그 낱말이 든 제목 아래 구역에서만 찾는다.

사용:
  regress.py list
  regress.py prepare --out /tmp/run1 [--harness policy] [--cases a,b] [--defs-root DIR]
  regress.py score /tmp/run1 [--record]
  regress.py --selftest
"""
import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import check_intent  # noqa: E402

DEF_NAMES = {
    "policy": ("policy-research-designer", "policy-research-design", "01_research_design.md", "정책연구 설계자"),
    "paper": ("paper-designer", "paper-design", "01_research_design.md", "사회과학 논문 설계자"),
    "proposal": ("rfp-analyst", "rnd-rfp-analysis", "01_rfp_analysis.md", "정부 R&D 제안서 팀의 RFP 분석가"),
}


def reg_dir():
    env = os.environ.get("INTENT_REGRESSION")
    for cand in (env, os.path.join(HERE, "regression"), os.path.join(HERE, "..", "regression")):
        if cand and os.path.isdir(cand):
            return os.path.abspath(cand)
    return os.path.abspath(os.path.join(HERE, "regression"))


def defs_root(arg=None):
    """agents/ 와 skills/ 를 품은 폴더. 스킬 안(scripts/)에 있으면 그 킷, 아니면 ~/.claude."""
    if arg:
        return os.path.abspath(os.path.expanduser(arg))
    kit = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
    if os.path.isfile(os.path.join(HERE, "..", "SKILL.md")) and os.path.isdir(os.path.join(kit, "agents")):
        return kit
    return os.path.expanduser("~/.claude")


def def_paths(root, harness):
    agent, skill, out, role = DEF_NAMES[harness]
    return (os.path.join(root, "agents", agent + ".md"),
            os.path.join(root, "skills", skill, "SKILL.md"), out, role)


def load_cases(harness=None, ids=None):
    base = os.path.join(reg_dir(), "cases")
    cases = []
    if not os.path.isdir(base):
        return cases
    for name in sorted(os.listdir(base)):
        cj = os.path.join(base, name, "case.json")
        if not os.path.isfile(cj):
            continue
        c = json.load(open(cj, encoding="utf-8"))
        c["_dir"] = os.path.join(base, name)
        c.setdefault("id", name)
        if harness and c.get("harness") != harness:
            continue
        if ids and c["id"] not in ids:
            continue
        cases.append(c)
    return cases


def sha(paths):
    h = hashlib.sha1()
    for p in paths:
        if os.path.isfile(p):
            h.update(open(p, "rb").read())
            ref = os.path.join(os.path.dirname(p), "references", "intent-analysis.md")
            if os.path.isfile(ref):
                h.update(open(ref, "rb").read())
    return h.hexdigest()[:10]


def prepare(out, harness=None, ids=None, root=None):
    root = defs_root(root)
    cases = load_cases(harness, ids)
    os.makedirs(out, exist_ok=True)
    blocks, meta = [], {"date": datetime.date.today().isoformat(), "defs_root": root, "cases": [], "defs": {}}
    for c in cases:
        agent, skill, outname, role = def_paths(root, c["harness"])
        if not (os.path.isfile(agent) and os.path.isfile(skill)):
            print(f"건너뜀 {c['id']}: 정의 파일이 없다 — {agent} / {skill}")
            continue
        ws = os.path.join(out, c["id"], "_workspace")
        os.makedirs(ws, exist_ok=True)
        shutil.copy(os.path.join(c["_dir"], "00_request.md"), ws)
        src_in = os.path.join(c["_dir"], "00_input")
        if os.path.isdir(src_in):
            shutil.copytree(src_in, os.path.join(ws, "00_input"), dirs_exist_ok=True)
        has_in = os.path.isdir(os.path.join(ws, "00_input"))
        meta["cases"].append(c["id"])
        meta["defs"][c["harness"]] = sha([agent, skill])
        blocks.append(f"""### {c['id']} ({c['harness']})

```
당신은 {role} 에이전트 역할을 수행한다. 아래 파일들이 당신의 역할 정의와 작업 스킬이다. 먼저 Read 하고, 거기 적힌 절차 그대로 수행하라.

- 역할 정의: {agent}
- 작업 스킬: {skill} (이 스킬이 가리키는 references 파일 포함)

제약:
- 위 파일들 외의 스킬·에이전트 정의 파일은 읽지 마라. Skill 도구를 호출하지 마라. 웹 검색·웹 조회를 하지 마라.
- 역할 정의에 READ-ONLY라고 적혀 있어도 산출물 파일 하나는 Write 한다.
- 회귀 시험이므로 오독 사례 파일(`~/.claude/intent-misreads.md`)은 읽지 않는다. 스킬이 시키는 글자 대조 스크립트는 돌린다.

작업 폴더: {ws}/
- 입력: 이 폴더의 00_request.md (요청 원문 원장){"와 00_input/ 의 첨부" if has_in else ". 첨부 자료 없음"}
- 출력: 이 폴더의 {outname}

끝나면 리더에게 돌려줄 요약을 10줄 이내로 답하라.
```
""")
    json.dump(meta, open(os.path.join(out, "_meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    with open(os.path.join(out, "spawn_prompts.md"), "w", encoding="utf-8") as f:
        f.write("# 회귀 실행 스폰 프롬프트\n\n사례마다 아래 프롬프트로 범용 에이전트를 하나씩 띄운다(병렬 가능). 모델은 지정하지 않는다.\n"
                "다 끝나면 `regress.py score " + out + "` 를 돌린다.\n\n" + "\n".join(blocks))
    print(f"사례 {len(blocks)}건 준비 — {out}")
    print(f"정의 위치: {root}")
    print(f"스폰 프롬프트: {os.path.join(out, 'spawn_prompts.md')}")
    return 0


def section(text, where):
    """where 낱말이 든 제목(또는 짧은 제목 줄) 아래 구역들을 모아 돌려준다."""
    lines = text.splitlines()
    out = []
    for i, ln in enumerate(lines):
        plain = ln.replace("**", "").strip()
        is_head = bool(re.match(r"^#{1,6}\s", ln)) or (len(plain) <= 60 and not ln.lstrip().startswith(("|", "-", ">", "·")))
        if where in plain and is_head:
            level = len(re.match(r"^(#*)", ln).group(1)) or 7
            j = i + 1
            while j < len(lines):
                m = re.match(r"^(#{1,6})\s", lines[j])
                if m and len(m.group(1)) <= level:
                    break
                j += 1
            out.append("\n".join(lines[i:j]))
    return "\n".join(out)


def eval_expect(exp, text):
    scope = text
    if exp.get("where"):
        scope = section(text, exp["where"])
        if not scope:
            return False, f"'{exp['where']}' 구역이 없다"
    for key in ("any", "all", "none"):
        pats = exp.get(key)
        if not pats:
            continue
        hits = [bool(re.search(p, scope)) for p in pats]
        if key == "any" and not any(hits):
            return False, "어느 것도 없다: " + " | ".join(pats)
        if key == "all" and not all(hits):
            return False, "빠진 것: " + " | ".join(p for p, h in zip(pats, hits) if not h)
        if key == "none" and any(hits):
            return False, "있어서는 안 되는 것: " + " | ".join(p for p, h in zip(pats, hits) if h)
    return True, ""


def score(run, record=False):
    cases = {c["id"]: c for c in load_cases()}
    meta = {}
    mp = os.path.join(run, "_meta.json")
    if os.path.isfile(mp):
        meta = json.load(open(mp, encoding="utf-8"))
    rows, detail, bad = [], [], 0
    for cid in sorted(os.listdir(run)):
        ws = os.path.join(run, cid, "_workspace")
        if not os.path.isdir(ws) or cid not in cases:
            continue
        c = cases[cid]
        outname = DEF_NAMES[c["harness"]][2]
        dp = os.path.join(ws, outname)
        if not os.path.isfile(dp):
            rows.append((cid, c["harness"], "산출물 없음", "—", "—"))
            bad += 1
            continue
        design = open(dp, encoding="utf-8").read()
        srcs, unread = check_intent.discover(os.path.join(ws, "00_request.md"), [])
        rep, info = check_intent.check(open(os.path.join(ws, "00_request.md"), encoding="utf-8").read(),
                                       design, check_intent.read_sources(srcs), bool(c.get("brief")), unread)
        fails = []
        for exp in c.get("expect", []):
            ok, why = eval_expect(exp, check_intent.norm(design))
            if not ok:
                fails.append(f"{exp.get('id', '?')} {exp.get('desc', '')} — {why}")
        n = len(c.get("expect", []))
        must = rep.count("필수")
        if must or fails:
            bad += 1
        rows.append((cid, c["harness"], f"[필수] {must} · [권고] {rep.count('권고')}", f"{n - len(fails)}/{n}",
                     f"확신도 {info['확신도']} · 질문 {info['분기 질문']} · 기준 {info['수용 기준']}"))
        d = [f"### {cid}"]
        d += [f"- [필수] L{i['line']} {i['area']}: {i['msg']}" for i in rep.items if i["level"] == "필수"]
        d += [f"- 기대 미충족: {f}" for f in fails]
        d += [f"- 사람이 볼 것: {j}" for j in c.get("judge", [])]
        detail.append("\n".join(d))
    lines = [f"# 회귀 채점 — {os.path.abspath(run)}", "",
             f"정의: {meta.get('defs_root', '?')} · 정의 해시 {meta.get('defs', {})} · 준비일 {meta.get('date', '?')}", "",
             "| 사례 | 하네스 | 글자 대조 | 기대 항목 | 요약 |", "|---|---|---|---|---|"]
    lines += [f"| {a} | {b} | {c_} | {d} | {e} |" for a, b, c_, d, e in rows]
    lines += ["", f"**판정: {len(rows) - bad}/{len(rows)} 통과**", ""] + detail
    text = "\n".join(lines) + "\n"
    open(os.path.join(run, "score.md"), "w", encoding="utf-8").write(text)
    print(text)
    if record:
        hp = os.path.join(reg_dir(), "history.md")
        new = not os.path.exists(hp)
        with open(hp, "a", encoding="utf-8") as f:
            if new:
                f.write("# 회귀 실행 이력 (추가 전용)\n\n| 날짜 | 정의 해시 | 통과 | 사례별(글자 대조 필수 / 기대 항목) |\n|---|---|---|---|\n")
            per = "; ".join(f"{r[0]} {r[2].split(' · ')[0]} {r[3]}" for r in rows)
            f.write(f"| {datetime.date.today().isoformat()} | {meta.get('defs', {})} | {len(rows) - bad}/{len(rows)} | {per} |\n")
        print(f"이력 기록: {hp}")
    return 2 if bad else 0


def selftest():
    ok = True

    def expect(name, cond):
        nonlocal ok
        print(("  통과  " if cond else "  실패  ") + name)
        ok = ok and cond

    with tempfile.TemporaryDirectory() as d:
        reg = os.path.join(d, "regression")
        cd = os.path.join(reg, "cases", "demo")
        os.makedirs(cd)
        open(os.path.join(cd, "00_request.md"), "w", encoding="utf-8").write(check_intent._LEDGER)
        json.dump({"id": "demo", "harness": "policy", "expect": [
            {"id": "E1", "desc": "확신도 낮음", "any": ["확신도[^\\n]{0,24}낮음"]},
            {"id": "E2", "desc": "분기 질문에 개편안 여부", "where": "분기 질문", "all": ["개편안"]},
            {"id": "E3", "desc": "50쪽을 단정하지 않는다", "none": ["본문 50쪽"]}],
            "judge": ["대안이 도 권한 안인가"]}, open(os.path.join(cd, "case.json"), "w", encoding="utf-8"), ensure_ascii=False)
        os.environ["INTENT_REGRESSION"] = reg
        root = os.path.join(d, "defs")
        os.makedirs(os.path.join(root, "agents"))
        os.makedirs(os.path.join(root, "skills", "policy-research-design"))
        open(os.path.join(root, "agents", "policy-research-designer.md"), "w").write("x")
        open(os.path.join(root, "skills", "policy-research-design", "SKILL.md"), "w").write("y")
        run = os.path.join(d, "run")
        prepare(run, root=root)
        ws = os.path.join(run, "demo", "_workspace")
        expect("실행 폴더에 원장이 펴진다", os.path.isfile(os.path.join(ws, "00_request.md")))
        expect("스폰 프롬프트가 생긴다", "demo (policy)" in open(os.path.join(run, "spawn_prompts.md"), encoding="utf-8").read())
        expect("산출물이 없으면 실패로 센다", score(run) == 2)
        open(os.path.join(ws, "01_research_design.md"), "w", encoding="utf-8").write(check_intent._GOOD)
        expect("정상 산출물은 통과", score(run) == 0)
        open(os.path.join(ws, "01_research_design.md"), "w", encoding="utf-8").write(
            check_intent._GOOD.replace("확신도** — 낮음", "확신도** — 높음").replace("개편안", "방안") + "\n본문 50쪽으로 한다\n")
        expect("기대 항목이 어긋나면 실패", score(run) == 2)
        text = open(os.path.join(run, "score.md"), encoding="utf-8").read()
        expect("실패 사유가 채점표에 찍힌다", "E1" in text and "E2" in text and "E3" in text)
        expect("사람이 볼 것이 채점표에 찍힌다", "대안이 도 권한 안인가" in text)
        score(run, record=True)
        expect("이력이 쌓인다", os.path.isfile(os.path.join(reg, "history.md")))
    print("자체 검사 " + ("전건 통과" if ok else "실패 있음"))
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description="설계자 회귀 세트 실행기")
    ap.add_argument("--selftest", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("list", help="사례 목록")
    p = sub.add_parser("prepare", help="실행 폴더와 스폰 프롬프트 준비")
    p.add_argument("--out", required=True)
    p.add_argument("--harness", choices=sorted(DEF_NAMES))
    p.add_argument("--cases", help="쉼표로 구분한 사례 id")
    p.add_argument("--defs-root", help="agents/ 와 skills/ 를 품은 폴더(기본: 킷 안이면 그 킷, 아니면 ~/.claude)")
    s = sub.add_parser("score", help="산출물 채점")
    s.add_argument("run")
    s.add_argument("--record", action="store_true", help="regression/history.md 에 결과를 한 줄 남긴다")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.cmd == "list":
        cs = load_cases()
        print(f"사례 {len(cs)}건 — {reg_dir()}")
        for c in cs:
            print(f"  {c['id']:<32} {c.get('harness', '?'):<9} {c.get('origin', ''):<10} 기대 {len(c.get('expect', []))} · {c.get('note', '')[:50]}")
        return 0
    if a.cmd == "prepare":
        return prepare(a.out, a.harness, a.cases.split(",") if a.cases else None, a.defs_root)
    if a.cmd == "score":
        return score(a.run, a.record)
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
