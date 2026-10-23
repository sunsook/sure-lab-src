"""요구사항 기반 시험(tests/TC-*.c)을 빌드해 돌린다.

컴파일러는 ziglang(`python -m ziglang cc`). 종료 코드 0 모두 PASS · 1 FAIL 있음 · 2 시험 자체 실패.
사용: python scripts/run_tests.py
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TC_FUNC = re.compile(r"^\s*int\s+(tc_\w+)\s*\(\s*void\s*\)", re.MULTILINE)


def error(msg):
    print(f"ERROR: {msg}")
    sys.exit(2)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        import ziglang  # noqa: F401
    except ImportError:
        error("ziglang 이 없다 — python -m pip install ziglang")

    tests = sorted((ROOT / "tests").glob("TC-*.c"))
    cases = []
    for path in tests:
        for name in TC_FUNC.findall(path.read_text(encoding="utf-8")):
            cases.append((path.stem, name))
    if not cases:
        error("tests/TC-*.c 에서 int tc_*(void) 시험 함수를 찾지 못했다")

    srcs = [p for p in sorted((ROOT / "src").glob("*.c")) if p.name != "main.c"]
    with tempfile.TemporaryDirectory() as tmp:
        runner = Path(tmp) / "runner.c"
        lines = ["#include <stdio.h>"]
        lines += [f"int {name}(void);" for _, name in cases]
        lines.append("int main(void) { int failed = 0, r;")
        for tc_id, name in cases:
            lines.append(f'  r = {name}(); printf("%s\\t%s\\n", "{tc_id}", r == 0 ? "PASS" : "FAIL"); failed += r != 0;')
        lines.append("  return failed; }")
        runner.write_text("\n".join(lines) + "\n", encoding="utf-8")

        exe = Path(tmp) / "run_tests.exe"
        cmd = [sys.executable, "-m", "ziglang", "cc", "-std=c11", "-I", str(ROOT / "include"),
               *map(str, srcs), *map(str, tests), str(runner), "-o", str(exe)]
        build = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if build.returncode != 0:
            print(build.stderr)
            error("빌드 실패")

        run = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        rows = [line.split("\t") for line in run.stdout.splitlines() if "\t" in line]
        if len(rows) != len(cases):
            print(run.stdout, run.stderr)
            error(f"시험 {len(cases)}건 중 {len(rows)}건만 결과를 냈다")

    print("| 시험 | 결과 |\n|---|---|")
    for tc_id, status in rows:
        print(f"| {tc_id} | {status} |")
    failed = sum(status != "PASS" for _, status in rows)
    print(f"\n{len(rows) - failed}/{len(rows)} PASS")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
