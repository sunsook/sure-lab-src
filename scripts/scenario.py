"""실습 결함판 브랜치를 만든다.

사용: python scripts/scenario.py b
  b — SR-002 경계 결함판: src/speed_monitor.c 의 「>= VSM_SPEED_LIMIT_KPH」를 「>」로 바꾼 커밋을 scenario/b 브랜치에 만든다.
      실습 2-4 에서 CT 목업 시험을 결함판에서 생성할 때 쓴다. 끝나면 git switch main 으로 돌아간다.
종료 코드: 0 만듦 · 2 만들지 못함(작업 트리 변경 · 브랜치 있음 · 바꿀 줄 없음 · 모르는 시나리오)
"""
import subprocess
import sys
from pathlib import Path

SCENARIOS = {
    "b": ("src/speed_monitor.c",
          "if (speed_kph >= VSM_SPEED_LIMIT_KPH)",
          "if (speed_kph > VSM_SPEED_LIMIT_KPH)",
          "scenario b: SR-002 경계 결함판(>= → >)"),
}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")


def fail(message):
    print(f"만들지 못함: {message}")
    return 2


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1 or argv[0] not in SCENARIOS:
        return fail(f"시나리오는 {', '.join(SCENARIOS)} 중 하나 — 예: python scripts/scenario.py b")
    name = argv[0]
    path, before, after, message = SCENARIOS[name]
    branch = f"scenario/{name}"
    if git("status", "--porcelain").stdout.strip():
        return fail("커밋하지 않은 변경이 있다 — 먼저 커밋하거나 정리한다")
    if git("branch", "--list", branch).stdout.strip():
        return fail(f"{branch} 브랜치가 이미 있다 — git switch {branch} 로 옮기거나 지운 뒤 다시 한다")
    file = Path(path)
    if not file.is_file():
        return fail(f"{path} 가 없다")
    with open(file, encoding="utf-8", newline="") as f:
        text = f.read()
    if text.count(before) != 1:
        return fail(f"{path} 에서 「{before}」 를 한 번 찾지 못했다 — 이미 결함판이거나 다른 판이다")
    base = git("branch", "--show-current").stdout.strip()
    if git("switch", "-c", branch).returncode != 0:
        return fail(f"{branch} 브랜치를 만들지 못했다")
    with open(file, "w", encoding="utf-8", newline="") as f:
        f.write(text.replace(before, after))
    commit = git("commit", "-q", "-m", message, "--", path)
    if commit.returncode != 0:
        git("checkout", "--", path)
        git("switch", base)
        git("branch", "-D", branch)
        return fail(f"커밋 실패 — {commit.stderr.strip()[:200]}")
    print(f"{branch} 를 만들었다({base} 에서) · {path}: 「{before}」 → 「{after}」")
    print(f"돌아갈 때: git switch {base}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
