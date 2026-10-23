#!/usr/bin/env python3
"""보호 Hook 결정 표 — .claude/settings.json 의 PreToolUse Hook 을 Claude Code 처럼 불러 hook_cases.json 과 대조한다.

AI 호출 0회 · 수 초. 2-2-2 에서 AI 가 만든 보호 Hook 이 「기존 시험 수정 · 삭제는 묻고, 새 시험은 묻지 않고,
어떤 입력에도 죽지 않는가」를 본다. Hook 이 죽으면(rc 0 · 2 가 아니면) Claude Code 는 오류만 보이고 도구를 그대로
실행한다 — 보호가 뚫린다(10/24 실측: 한글 명령 · 따옴표 안 ; 에서 생성 Hook 둘이 각각 놓침).

부르는 꼴: Git Bash 로 Hook 명령을 돌리고 · stdin 에 UTF-8 JSON · CLAUDE_PROJECT_DIR · PYTHONUTF8 없음(수강생 자리 기본).
저장소를 임시 폴더에 복사해 그 안에서 돈다 — Hook 이 남기는 로그 · 시험용 새 파일이 이 저장소에 남지 않는다.

사용: python scripts/check_hook.py [--root .] [--cases scripts/hook_cases.json] [--json]
종료 코드: 0 모두 PASS · 1 FAIL 있음 · 2 입력 오류(settings.json · 사례 파일 · bash 없음)
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIORITY = ["block", "deny", "ask", "allow", "pass"]  # 여러 Hook 이 다르게 답하면 앞쪽이 이긴다


def find_bash():
    cands = [os.environ.get("HOOK_BASH"), r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"]
    for c in cands:
        if c and Path(c).is_file():
            return c
    found = shutil.which("bash")
    if found and "system32" not in found.lower():  # Windows 의 System32\bash.exe 는 WSL — Claude Code 가 쓰는 셸이 아니다
        return found
    return None


def subst(value, root):
    if isinstance(value, str):
        return value.replace("{root}", root)
    if isinstance(value, list):
        return [subst(v, root) for v in value]
    if isinstance(value, dict):
        return {k: subst(v, root) for k, v in value.items()}
    return value


def hooks_for(settings, tool):
    out = []
    for entry in settings.get("hooks", {}).get("PreToolUse", []):
        matcher = entry.get("matcher") or "*"
        if matcher == "*" or re.fullmatch(f"(?:{matcher})", tool):
            out += [h["command"] for h in entry.get("hooks", []) if h.get("type") == "command" and h.get("command")]
    return out


def run_case(case, repo, settings, bash, base_env):
    root = str(repo)
    tool = case["tool"]
    payload = {"session_id": "check_hook", "cwd": root, "permission_mode": "bypassPermissions",
               "hook_event_name": "PreToolUse", "tool_name": tool}
    if case.get("input") is not None:
        payload["tool_input"] = subst(case["input"], root)
    stdin = case["stdin_raw"].encode("utf-8") if "stdin_raw" in case else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    env = {**base_env, "CLAUDE_PROJECT_DIR": root, **subst(case.get("env", {}), root)}
    made = []
    for rel in case.get("setup", {}).get("untracked", []):
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("/* draft */\n", encoding="utf-8")
        made.append(p)
    decisions, broken = [], []
    try:
        for cmd in hooks_for(settings, tool):
            try:
                r = subprocess.run([bash, "-c", cmd], input=stdin, capture_output=True, cwd=root, env=env, timeout=30)
            except subprocess.TimeoutExpired:
                broken.append("30초 넘음")
                continue
            if r.returncode == 2:
                decisions.append("block")
                continue
            if r.returncode != 0:
                tail = r.stderr.decode("utf-8", "replace").strip().splitlines()
                broken.append(f"rc={r.returncode}: {tail[-1] if tail else ''}"[:160])
                continue
            out = r.stdout.decode("utf-8", "replace").strip()
            if not out:
                decisions.append("pass")
                continue
            try:
                d = json.loads(out).get("hookSpecificOutput", {}).get("permissionDecision") or "pass"
            except (ValueError, AttributeError):
                broken.append(f"stdout 이 JSON 이 아님: {out[:60]}")
                continue
            decisions.append(d)
    finally:
        for p in made:
            p.unlink(missing_ok=True)
    if broken:
        got = "고장 — " + " / ".join(broken)
    else:
        got = next((d for d in PRIORITY if d in decisions), "pass")
    expect = case["expect"]
    if broken:
        ok = False
    elif expect == "nocrash":
        ok = got not in ("block", "allow")
    else:
        ok = got == expect
    return {"id": case["id"], "what": case["what"], "expect": expect, "got": got, "ok": ok}


def on_rm_error(func, path, _):
    os.chmod(path, stat.S_IWRITE)  # .git 안 읽기 전용 파일
    func(path)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="보호 Hook 결정 표")
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--cases", default=str(HERE / "hook_cases.json"))
    ap.add_argument("--json", action="store_true", help="결과를 JSON 목록으로만 출력")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    settings_path = root / ".claude" / "settings.json"
    if not settings_path.is_file():
        print(f"입력 오류: {settings_path} 없음 — .claude/settings.json 에 PreToolUse Hook 을 먼저 건다")
        return 2
    try:
        settings = json.loads(settings_path.read_text(encoding="utf-8"))
        cases = json.loads(Path(a.cases).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        print(f"입력 오류: settings.json 또는 사례 파일을 읽지 못함 — {e}")
        return 2
    bash = find_bash()
    if not bash:
        print("입력 오류: Git Bash 를 찾지 못함(HOOK_BASH 로 경로를 줄 수 있음)")
        return 2
    base_env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
    tmp = Path(tempfile.mkdtemp(prefix="check_hook_"))
    try:
        repo = tmp / "repo"
        shutil.copytree(root, repo, ignore=shutil.ignore_patterns("out", ".review", "__pycache__", "node_modules"))
        rows = [run_case(c, repo, settings, bash, base_env) for c in cases]
    finally:
        shutil.rmtree(tmp, onerror=on_rm_error)
    if a.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print("| 사례 | 무엇 | 기대 | 결과 | 판정 |\n|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['id']} | {r['what']} | {r['expect']} | {r['got']} | {'PASS' if r['ok'] else 'FAIL'} |")
        bad = [r["id"] for r in rows if not r["ok"]]
        print(f"\n{len(rows) - len(bad)}/{len(rows)} PASS" + (f" — FAIL: {', '.join(bad)}" if bad else ""))
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
