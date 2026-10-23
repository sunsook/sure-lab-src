# VSM 실습 소스 템플릿 — Agentic AI 기반 SW 품질 검증 자동화 (2 · 3일차)

> 교육용 배포판 — 개인 용도로 쓰고 재배포는 문의 바랍니다.

차량 속도 감시(VSM) C 코드 · 요구사항 · 시험이 들어 있는 소스 템플릿이다. 이 저장소를 「Use this template」로 내 예제코드저장소(lab1-code · Private)로 만든 뒤, 클론한 폴더에서 `claude` 를 연다.

## 필요한 도구

| 도구 | 확인 명령 | 없을 때 |
|---|---|---|
| git | `git --version` | Git for Windows 설치 — Claude Code 보다 먼저 |
| gh (GitHub CLI) | `gh --version` · `gh auth status` | 설치 후 `gh auth login` |
| Python 3.10+ | `python --version` | python.org 설치본 |
| ziglang (C 컴파일러) · pycparser · PyYAML · pytest | `python -m ziglang version` · `python -m pip show pycparser pyyaml pytest` | `python -m pip install -r requirements.txt` |
| git 첫 설정 | `git config --global user.name` · `git config --global user.email` | GitHub 가입 계정의 이름과 이메일로 설정 |
| jq | `jq --version` | 설치 — 새 터미널부터 잡힌다 |
| Claude Code (로그인) | `claude --version` | PowerShell `irm https://claude.ai/install.ps1 \| iex` 뒤 새 터미널에서 `claude` → 지급 계정으로 로그인 |

셋업은 클론한 폴더에서 `claude` 를 열고 한 줄로 시킨다 — 「`docs/SETUP.md` 대로 셋업해 줘」. 준비 끝은 `python scripts/setup_check.py` 가 모든 줄 `OK` · 종료 코드 0 이다.

막히면 — Claude Code 설치 전에는 Claude 데스크톱 앱에 오류 메시지와 함께 묻고, 설치 뒤에는 Claude Code 에서 바로 묻는다.

## 실습 저장소 셋

| 내 저장소(Private) | 만드는 법 |
|---|---|
| 예제코드저장소 `lab1-code` | 이 템플릿으로 「Use this template」 |
| PR리뷰어저장소 `lab2-reviewer` | 빈 저장소 |
| CICD저장소 `lab3-cicd` | 빈 저장소 |

## 모듈 설치 소스

모듈에서 AI 에게 「<원천> 을 이 저장소에 설치해 줘」로 시킨다. 설치 절차는 각 원천의 README 에 있다.

| 원천 | 주소 | 설치하는 저장소 · 때 |
|---|---|---|
| Harness | https://github.com/sunsook/sure-lab-harness | lab1-code 2-2-준비-1 · lab2-reviewer 2-4-준비-2 · lab3-cicd 3-2-1 전 |
| Harness Eval | https://github.com/sunsook/sure-lab-eval | lab1-code 2-3-준비-1 · lab2-reviewer 2-4-준비-2 |
| 검증 도구(목업) | https://github.com/sunsook/sure-lab-tools | lab1-code 2-4-준비-1 · lab3-cicd 3-3 |

## 들어 있는 것

| 경로 | 무엇 |
|---|---|
| `src/` · `include/` | VSM C 소스 |
| `tests/` | 시험 |
| `docs/요구사항.md` | 요구사항 SR-001~011 |
| `docs/SETUP.md` | 셋업 절차 |
| `scripts/run_tests.py` · `setup_check.py` | 시험 실행 · 셋업 점검(읽기 전용) |
| `scripts/scenario.py` | 실습 결함판 브랜치 — `python scripts/scenario.py b` = SR-002 경계 결함판(`scenario/b`) · 2-4 에서 CT 목업 시험을 결함판에서 생성할 때 |
