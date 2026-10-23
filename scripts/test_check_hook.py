"""check_hook.py 시험 — 임시 git 저장소에 가짜 보호 Hook 을 걸고 결정 표가 결함을 잡는지 본다.

가짜 Hook 다섯: 안 묻기 · 다 묻기 · 한글에서 죽기(10/24 2회차 꼴) · 따옴표 안 ; 로 놓치기(10/24 1회차 꼴) · 기준.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
SCRIPT = HERE / "check_hook.py"
CASES = HERE / "hook_cases.json"

NEVER = "import sys\nsys.stdin.buffer.read()\n"
ALWAYS = (
    "import json, sys\nsys.stdin.buffer.read()\n"
    "print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'ask',"
    " 'permissionDecisionReason': 'x'}}))\n"
)
# 10/24 2회차 꼴 — 표준입력을 기본 인코딩으로 읽고, 걸린 명령을 UTF-8 로그에 쓴다(한글이면 죽는다)
CRASH = (
    "import json, os, sys\n"
    "d = json.load(sys.stdin)\nti = d.get('tool_input') or {}\n"
    "s = ti.get('command') or ti.get('file_path') or ''\n"
    "if 'tests' in s:\n"
    "    os.makedirs('out', exist_ok=True)\n"
    "    open('out/log.txt', 'a', encoding='utf-8').write(s[:80] + '\\n')\n"
    "    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'ask',"
    " 'permissionDecisionReason': 'x'}}))\n"
)
# 10/24 1회차 꼴 — 명령을 ; 로 나눠 조각마다 「동사 + tests/」를 찾는다(따옴표 안 ; 에서 놓친다)
SEMICOLON = (
    "import json, re, sys\n"
    "d = json.loads(sys.stdin.buffer.read().decode('utf-8'))\nti = d.get('tool_input') or {}\n"
    "hit = False\n"
    "if d.get('tool_name') in ('Edit', 'MultiEdit', 'Write'):\n"
    "    p = ti.get('file_path', '').replace('\\\\', '/')\n"
    "    hit = '/tests/' in '/' + p and not p.endswith('_new.c')\n"
    "else:\n"
    "    for seg in ti.get('command', '').split(';'):\n"
    "        if re.search(r'(sed\\s+-i|rm |git\\s+rm|>|Set-Content|git\\s+checkout)', seg) and re.search(r'tests[/\\\\]TC-02b', seg):\n"
    "            hit = True\n"
    "if hit:\n"
    "    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PreToolUse', 'permissionDecision': 'ask',"
    " 'permissionDecisionReason': 'x'}}))\n"
)
# 기준 — 표준입력을 UTF-8 로 읽고 · git 이 추적하는 tests/ 파일만 · 어떤 오류든 묻기로
GOOD = r'''
import json, os, re, subprocess, sys

def ask(reason):
    # ensure_ascii 기본값(\uXXXX) — Windows 파이프 stdout 은 cp949 라 한글 · 「—」를 그대로 찍으면 죽는다(기준 Hook 첫 판이 실제로 죽음)
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
          "permissionDecision": "ask", "permissionDecisionReason": reason}}))

def tracked_test(path, root):
    rel = os.path.relpath(os.path.join(root, path), root) if not os.path.isabs(path) else os.path.relpath(path, root)
    rel = rel.replace("\\", "/")
    if not rel.startswith("tests/"):
        return False
    r = subprocess.run(["git", "ls-files", "--", rel], cwd=root, capture_output=True, text=True)
    return r.returncode != 0 or bool(r.stdout.strip())

def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        tool, ti = data.get("tool_name", ""), data.get("tool_input") or {}
        root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or "."
        if tool in ("Edit", "MultiEdit", "Write"):
            hit = tracked_test(ti.get("file_path", ""), root)
        elif tool in ("Bash", "PowerShell"):
            cmd = ti.get("command", "")
            verbs = re.search(r"(sed\s+-i|\brm\b|git\s+(rm|mv|checkout|restore)|>|Set-Content|Out-File|\bmv\b|\bcp\b)", cmd)
            hit = bool(verbs) and any(tracked_test(p, root) for p in re.findall(r"tests[/\\][\w.\-]+", cmd))
        else:
            hit = False
        if hit:
            ask("기존 시험 수정 — 확인 필요")
    except Exception as e:
        ask(f"Hook 오류 — 확인 필요 ({type(e).__name__})")
    return 0

sys.exit(main())
'''


def git(repo, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=repo,
                          capture_output=True, text=True, encoding="utf-8")


def make_repo(tmp_path, hook_src):
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "TC-02b_sr002_boundary.c").write_text("int tc_02b(void) { return 0; }\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "speed_monitor.c").write_text("int f(void) { return 1; }\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "hook.py").write_text(hook_src, encoding="utf-8")
    settings = {"hooks": {"PreToolUse": [{"matcher": "Edit|MultiEdit|Write|Bash|PowerShell", "hooks": [
        {"type": "command", "command": 'cd "$CLAUDE_PROJECT_DIR" && python .claude/hook.py'}]}]}}
    (tmp_path / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def run(repo):
    p = subprocess.run([sys.executable, str(SCRIPT), "--root", str(repo), "--cases", str(CASES), "--json"],
                       capture_output=True, text=True, encoding="utf-8")
    rows = json.loads(p.stdout) if p.stdout.strip().startswith("[") else []
    return p.returncode, {r["id"]: r for r in rows}, p


def failed(rows):
    return {i for i, r in rows.items() if not r["ok"]}


def test_good_hook_passes_every_case(tmp_path):
    rc, rows, p = run(make_repo(tmp_path, GOOD))
    assert rows, p.stdout + p.stderr
    assert failed(rows) == set(), {i: rows[i] for i in failed(rows)}
    assert rc == 0


def test_never_asking_hook_fails_every_ask_case(tmp_path):
    rc, rows, _ = run(make_repo(tmp_path, NEVER))
    asks = {i for i, r in rows.items() if r["expect"] == "ask"}
    assert asks and asks <= failed(rows)
    assert rc == 1


def test_always_asking_hook_fails_tdd_cases(tmp_path):
    rc, rows, _ = run(make_repo(tmp_path, ALWAYS))
    assert {"P01", "P02"} <= failed(rows)  # 새 시험 파일 · 커밋 전 새 시험 — TDD 가 막힌다
    assert rc == 1


def test_korean_crash_hook_is_reported_broken(tmp_path):
    rc, rows, _ = run(make_repo(tmp_path, CRASH))
    assert {"A07", "A08"} <= failed(rows)
    assert "rc=1" in rows["A07"]["got"]
    assert rows["A05"]["ok"]  # 영어 명령은 잡는다 — 한글에서만 죽는다
    assert rc == 1


def test_semicolon_hook_misses_quoted_semicolon(tmp_path):
    rc, rows, _ = run(make_repo(tmp_path, SEMICOLON))
    assert "A06" in failed(rows)
    assert rows["A05"]["ok"]
    assert rc == 1


def test_missing_settings_is_input_error(tmp_path):
    repo = make_repo(tmp_path, GOOD)
    (repo / ".claude" / "settings.json").unlink()
    rc, _, p = run(repo)
    assert rc == 2, p.stdout + p.stderr
    assert "settings.json" in p.stdout + p.stderr  # 「파일 없음」 같은 다른 rc 2 와 가린다
