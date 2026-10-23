"""scenario.py 시험 — 임시 git 저장소에서 결함판 브랜치를 만든다."""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).with_name("scenario.py")
LINE = "    if (speed_kph >= VSM_SPEED_LIMIT_KPH)\n"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, encoding="utf-8")


def make_repo(tmp_path, line=LINE):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "speed_monitor.c").write_text("int f(void)\n{\n" + line + "    return 1;\n}\n", encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    return tmp_path


def run(repo, *args):
    env_args = [sys.executable, str(SCRIPT), *args]
    return subprocess.run(env_args, cwd=repo, capture_output=True, text=True, encoding="utf-8",
                          env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                               "GIT_COMMITTER_EMAIL": "t@t", **__import__("os").environ})


def test_b_makes_branch_with_boundary_defect(tmp_path):
    repo = make_repo(tmp_path)
    p = run(repo, "b")
    assert p.returncode == 0, p.stdout + p.stderr
    assert git(repo, "branch", "--show-current").stdout.strip() == "scenario/b"
    text = (repo / "src" / "speed_monitor.c").read_text(encoding="utf-8")
    assert "speed_kph > VSM_SPEED_LIMIT_KPH" in text and ">=" not in text
    assert git(repo, "status", "--porcelain").stdout == ""
    assert git(repo, "rev-list", "--count", "main..scenario/b").stdout.strip() == "1"


def test_b_refuses_when_line_missing(tmp_path):
    repo = make_repo(tmp_path, line="    if (speed_kph > VSM_SPEED_LIMIT_KPH)\n")
    p = run(repo, "b")
    assert p.returncode == 2
    assert git(repo, "branch", "--list", "scenario/b").stdout.strip() == ""


def test_b_refuses_dirty_tree(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "x.txt").write_text("x", encoding="utf-8")
    p = run(repo, "b")
    assert p.returncode == 2


def test_unknown_scenario(tmp_path):
    repo = make_repo(tmp_path)
    assert run(repo, "z").returncode == 2
