"""Setup checks use injected command and PATH results, never real installers."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import setup_check


def passing_tools():
    found = {name: f"C:/tools/{name}.exe" for name in ("git", "gh", "jq", "claude")}
    replies = {
        ("git", "--version"): "git version 2.50.0",
        ("gh", "--version"): "gh version 2.70.0",
        ("gh", "auth", "status"): "Logged in to github.com",
        (sys.executable, "--version"): "Python 3.12.0",
        (sys.executable, "-c", "import yaml; print(yaml.__version__)"): "6.0.2",
        (sys.executable, "-m", "ziglang", "version"): "0.13.0",
        (sys.executable, "-c", "import pytest; print(pytest.__version__)"): "8.4.0",
        (sys.executable, "-c", "import pycparser; print(pycparser.__version__)"): "2.22",
        ("gh", "repo", "view", "--json", "viewerPermission", "-q", ".viewerPermission"): "ADMIN",
        ("jq", "--version"): "jq-1.7",
        ("claude", "--version"): "2.0.0",
        ("git", "config", "user.name"): "Student",
        ("git", "config", "user.email"): "student@example.com",
        ("git", "config", "core.autocrlf"): "true",
        (sys.executable, str(setup_check.RUN_TESTS)): "| 시험 | 결과 |\n|---|---|\n| TC-02b_sr002_boundary | PASS |\n\n1/1 PASS",
    }

    def which(name):
        return found.get(name)

    def run(command):
        command = tuple(command)
        if command not in replies:
            raise AssertionError(f"Unexpected command: {command}")
        answer = replies[command]
        if isinstance(answer, Exception):
            raise answer
        if isinstance(answer, tuple):
            code, output = answer
        else:
            code, output = 0, answer
        return subprocess.CompletedProcess(command, code, output, "")

    return found, replies, which, run


def test_setup_check_all_ok_exit0(capsys):
    _, _, which, run = passing_tools()
    assert setup_check.check_setup(which, run) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 15
    assert all(line.startswith("OK ") for line in lines)
    assert "OK run_tests.py (1/1 PASS)" in lines
    assert "OK push 권한 (ADMIN)" in lines


def test_setup_check_reports_missing(capsys):
    found, _, which, run = passing_tools()
    del found["jq"]
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 jq → winget install jqlang.jq" in capsys.readouterr().out


def test_setup_check_empty_git_user(capsys):
    _, replies, which, run = passing_tools()
    replies[("git", "config", "user.name")] = ""
    replies[("git", "config", "user.email")] = ""
    assert setup_check.check_setup(which, run) == 1
    output = capsys.readouterr().out
    assert '빠짐 git user.name → git config --global user.name "<GitHub 이름>"' in output
    assert '빠짐 git user.email → git config --global user.email "<GitHub 이메일>"' in output


def test_setup_check_python_too_old(capsys):
    _, replies, which, run = passing_tools()
    replies[(sys.executable, "--version")] = "Python 3.9.21"
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 Python 3.10+" in capsys.readouterr().out


def test_setup_check_gh_not_logged_in(capsys):
    _, replies, which, run = passing_tools()
    replies[("gh", "auth", "status")] = (1, "not logged in")
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 gh 로그인 → gh auth login" in capsys.readouterr().out


def test_setup_check_missing_pip_package(capsys):
    _, replies, which, run = passing_tools()
    replies[(sys.executable, "-c", "import yaml; print(yaml.__version__)")] = (1, "No module named yaml")
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 pyyaml → python -m pip install -r requirements.txt" in capsys.readouterr().out


def test_setup_check_missing_pycparser(capsys):
    _, replies, which, run = passing_tools()
    replies[(sys.executable, "-c", "import pycparser; print(pycparser.__version__)")] = (1, "No module named pycparser")
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 pycparser → python -m pip install -r requirements.txt" in capsys.readouterr().out


def test_setup_check_push_read_only(capsys):
    _, replies, which, run = passing_tools()
    replies[("gh", "repo", "view", "--json", "viewerPermission", "-q", ".viewerPermission")] = "READ"
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 push 권한" in capsys.readouterr().out


def test_setup_check_run_tests_fail_reports_last_line(capsys):
    _, replies, which, run = passing_tools()
    replies[(sys.executable, str(setup_check.RUN_TESTS))] = (1, "| 시험 | 결과 |\n|---|---|\n| TC-02b_sr002_boundary | FAIL |\n\n0/1 PASS")
    assert setup_check.check_setup(which, run) == 1
    output = capsys.readouterr().out
    assert "빠짐 run_tests.py" in output
    assert "0/1 PASS" in output


def test_setup_check_command_exception_is_missing(capsys):
    _, replies, which, run = passing_tools()
    replies[("jq", "--version")] = subprocess.TimeoutExpired("jq", 10)
    assert setup_check.check_setup(which, run) == 1
    assert "빠짐 jq" in capsys.readouterr().out
