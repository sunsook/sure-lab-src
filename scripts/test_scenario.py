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


def test_b_commit_message_does_not_reveal_defect(tmp_path):
    # 2-4ⓑ 리뷰어는 커밋 메시지도 읽는다 — 「결함판 · >= → >」가 보이면 리뷰가 오염된다(10/24 실측)
    repo = make_repo(tmp_path)
    assert run(repo, "b").returncode == 0
    msg = git(repo, "log", "-1", "--format=%B").stdout
    assert not any(w in msg for w in ("결함", "SR-", ">=", "→", "scenario"))


M_LINE = "    for (i = 0u; i < count; i++)\n"


def make_filter_repo(tmp_path, line=M_LINE):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "sensor_filter.c").write_text(
        "int16_t sf_average(int16_t *samples, uint8_t count)\n{\n" + line + "    {\n    }\n    return 0;\n}\n",
        encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "add", ".")
    git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "init")
    return tmp_path


def test_m_makes_branch_with_sizeof_on_array_parameter(tmp_path):
    # MISRA 12.5(Mandatory) — 배열 매개변수에 sizeof · 「이 PR 은 Merge 불가」 장면(C2-3 5-0 #2)
    repo = make_filter_repo(tmp_path)
    p = run(repo, "m")
    assert p.returncode == 0, p.stdout + p.stderr
    assert git(repo, "branch", "--show-current").stdout.strip() == "scenario/m"
    text = (repo / "src" / "sensor_filter.c").read_text(encoding="utf-8")
    assert "sizeof(samples)" in text and "i < count" not in text
    msg = git(repo, "log", "-1", "--format=%B").stdout
    assert not any(w in msg for w in ("결함", "MISRA", "12.5", "scenario"))


def test_unknown_scenario(tmp_path):
    repo = make_repo(tmp_path)
    assert run(repo, "z").returncode == 2
