"""Read-only prerequisite checks for a fresh VSM lab machine."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

RUN_TESTS = Path(__file__).resolve().parent / "run_tests.py"
PUSH_OK = {"ADMIN", "MAINTAIN", "WRITE"}


def run_command(command, timeout=15):
    """Run a read-only probe with bounded time and UTF-8 output."""
    return subprocess.run(
        command, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=timeout, check=False,
    )


def check_setup(which=shutil.which, run=run_command, run_long=None):
    """Print each check and return 0 only when every prerequisite passes.

    `which` and `run` are injectable so tests do not call installed tools.
    `run_long` runs the C build and tests — the first zig build on a new PC is slow.
    """
    missing = False
    if run_long is None:
        run_long = (lambda command: run_command(command, timeout=300)) if run is run_command else run

    def report(name, command, remedy, valid=None, runner=None, last=False):
        nonlocal missing
        try:
            result = (runner or run)(command)
            value = (result.stdout.strip() or result.stderr.strip()).splitlines()
            value = value[-1 if last else 0].strip() if value else ""
            if result.returncode != 0:
                reason = value or f"exit {result.returncode}"
            elif not value:
                reason = "빈 출력"
            elif valid is not None and not valid(value):
                reason = f"확인 실패: {value}"
            else:
                print(f"OK {name} ({value})")
                return
        except (OSError, subprocess.TimeoutExpired) as exc:
            reason = f"{type(exc).__name__}: {exc}"
        print(f"빠짐 {name} → {remedy} (사유: {reason})")
        missing = True

    def tool(name, remedy):
        nonlocal missing
        try:
            found = which(name)
        except OSError as exc:
            found = None
            reason = f" (사유: {type(exc).__name__}: {exc})"
        else:
            reason = ""
        if not found:
            print(f"빠짐 {name} → {remedy}{reason}")
            missing = True
        return bool(found)

    git = tool("git", "winget install Git.Git")
    if git:
        report("git", ["git", "--version"], "winget install Git.Git")

    gh = tool("gh", "winget install GitHub.cli")
    if gh:
        report("gh", ["gh", "--version"], "winget install GitHub.cli")
        report("gh 로그인", ["gh", "auth", "status"], "gh auth login (브라우저 인증은 사람)")
        report("push 권한", ["gh", "repo", "view", "--json", "viewerPermission", "-q", ".viewerPermission"],
               "내 GitHub 저장소(Use this template 로 만든 것)를 클론한 폴더인지 · gh auth login", lambda v: v in PUSH_OK)
    else:
        print("빠짐 gh 로그인 → gh auth login (브라우저 인증은 사람) (사유: gh 없음)")
        print("빠짐 push 권한 → gh 설치 · 로그인 뒤 다시 점검 (사유: gh 없음)")
        missing = True

    def modern_python(value):
        match = re.match(r"Python (\d+)\.(\d+)", value)
        return bool(match and tuple(map(int, match.groups())) >= (3, 10))

    report("Python 3.10+", [sys.executable, "--version"], "winget install Python.Python.3.12", modern_python)

    package_remedy = "python -m pip install -r requirements.txt"
    report("pyyaml", [sys.executable, "-c", "import yaml; print(yaml.__version__)"], package_remedy)
    report("ziglang", [sys.executable, "-m", "ziglang", "version"], package_remedy)
    report("pytest", [sys.executable, "-c", "import pytest; print(pytest.__version__)"], package_remedy)
    report("pycparser", [sys.executable, "-c", "import pycparser; print(pycparser.__version__)"], package_remedy)

    if tool("jq", "winget install jqlang.jq"):
        report("jq", ["jq", "--version"], "winget install jqlang.jq")
    if tool("claude", "irm https://claude.ai/install.ps1 | iex"):
        report("claude", ["claude", "--version"], "irm https://claude.ai/install.ps1 | iex")

    if git:
        report("git user.name", ["git", "config", "user.name"], 'git config --global user.name "<GitHub 이름>"')
        report("git user.email", ["git", "config", "user.email"], 'git config --global user.email "<GitHub 이메일>"')
        report("core.autocrlf", ["git", "config", "core.autocrlf"], "git config --global core.autocrlf true")
    else:
        for name, remedy in (
            ("git user.name", 'git config --global user.name "<GitHub 이름>"'),
            ("git user.email", 'git config --global user.email "<GitHub 이메일>"'),
            ("core.autocrlf", "git config --global core.autocrlf true"),
        ):
            print(f"빠짐 {name} → {remedy} (사유: git 없음)")

    report("run_tests.py", [sys.executable, str(RUN_TESTS)],
           "위 빠짐을 먼저 해결 — 그래도 실패하면 출력 전문을 강사에게", runner=run_long, last=True)

    return 1 if missing else 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return check_setup()


if __name__ == "__main__":
    sys.exit(main())
