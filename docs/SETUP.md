# Claude용 사전 설치 절차

이 저장소를 복사한 수강생의 Windows PC에서 저장소 루트를 작업 폴더로 삼아 진행한다. 점검 스크립트는 읽기 전용이다. 설치와 계정 설정 명령은 실행 전에 수강생에게 보여 주고 승인을 받는다. 브라우저 인증은 수강생이 직접 한다.

gcc · MinGW · Visual Studio Build Tools 는 설치하지 않는다. C 빌드는 ziglang 으로 하고, 커버리지는 CI 에서만 잰다.

1. `python scripts/setup_check.py`를 실행하고 종료 코드와 모든 `빠짐` 줄을 읽는다. Python 명령 자체가 실행되지 않으면 Python 3.10 이상 설치가 먼저 필요하다고 보고한다. 스크립트가 예외로 끝나면 오류 전문을 보고하고 멈춘다.
2. 빠진 도구별 설치 명령을 수강생에게 보여 주고 승인받은 뒤 실행한다. `git`: `winget install Git.Git`; `gh`: `winget install GitHub.cli`; Python: `winget install Python.Python.3.12`; `jq`: `winget install jqlang.jq`; Claude Code: PowerShell에서 `irm https://claude.ai/install.ps1 | iex`. 설치 뒤 새 터미널을 열어 PATH에 잡히는지 확인한다. `winget`이 없거나 설치가 실패하면 명령과 오류를 보고하고 멈춘다. 임의의 다른 설치 경로를 조용히 실행하지 않는다.
3. Git 첫 설정을 확인한다. `git config user.name`, `git config user.email`, `git config core.autocrlf` 값을 본다. 이름과 이메일이 비어 있으면 수강생의 **GitHub 가입 계정**에 사용할 이름과 이메일을 확인받고, 명령을 보여 주어 승인받은 뒤 `git config --global user.name "<GitHub 이름>"`, `git config --global user.email "<GitHub 이메일>"`을 실행한다. `core.autocrlf`가 비어 있으면 승인받은 뒤 `git config --global core.autocrlf true`를 실행한다. 값을 알 수 없거나 명령이 실패하면 사유를 보고하고 멈춘다.
4. `gh auth status`가 실패하면 `gh auth login`을 안내하고 실행 전에 승인받는다. 브라우저가 열리면 수강생의 인증을 기다린다. 완료 후 `gh auth status`로 확인한다. 인증이 취소되거나 계속 실패하면 그 결과를 보고하고 멈춘다. 암호나 인증 코드를 대신 입력하지 않는다.
   `push 권한`이 `빠짐`이면 `git remote -v`를 보여 주고 멈춘다. 이 폴더가 수강생이 「Use this template」로 만든 자기 GitHub 저장소를 클론한 것인지 수강생이 확인한다. 저장소를 새로 만들거나 원격을 바꾸는 일은 수강생 승인 뒤에만 한다.
5. `python -m pip install -r requirements.txt`를 수강생에게 보여 주고 승인받은 뒤 실행한다. 이 명령은 PyYAML, ziglang, pytest, pycparser를 설치한다. 실패하면 pip 오류 전문을 보고하고 멈춘다.
6. `python scripts/setup_check.py`를 다시 실행한다. 이 스크립트는 마지막에 `python scripts/run_tests.py`도 돌린다(새 PC의 첫 실행은 zig 가 준비하느라 몇십 초 걸릴 수 있다). 종료 코드 0이고 모든 항목이 `OK`인지 확인한다. `빠짐`이 남으면 해당 줄과 실행한 해결 명령의 결과를 보고한다. 해결할 수 있는 다음 항목을 같은 절차로 처리한 뒤 재점검한다. 사용자 인증, 설치 승인, 계정 정보가 필요한 지점에서는 수강생의 응답을 기다린다. 최종 exit 0이 되지 않으면 완료라고 말하지 않는다.
7. 끝나면 결과를 표 하나로 보여 준다: 항목 | 값 | 상태. 새로 설치한 도구가 있으면 「새 터미널을 열고 claude 를 다시 연다」고 알린다.
