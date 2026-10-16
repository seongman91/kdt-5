# 7교시. VS Code에서 watsonx Orchestrate ADK 실행하기

## 1. 실습 목표

이번 실습에서는 VS Code에서 IBM watsonx Orchestrate ADK 개발 환경을 설정하고, 간단한 Python Tool을 작성한 뒤 watsonx Orchestrate 환경에 등록하는 흐름을 확인합니다.

이 시간의 목표는 복잡한 Agent를 완성하는 것이 아니라, **ADK가 어떤 방식으로 Agent와 Tool을 코드 기반으로 확장하는지 이해하는 것**입니다.

---

## 2. ADK란?

ADK는 **Agent Development Kit**의 약자로, watsonx Orchestrate에서 Agent와 Tool을 개발하기 위한 개발자용 도구입니다.

앞 시간까지는 Agent Builder 화면에서 Agent를 만들었다면, ADK를 사용하면 다음과 같은 작업을 코드 기반으로 수행할 수 있습니다.

* Python으로 Tool 작성
* YAML/JSON/Python 파일로 Agent 정의
* CLI 명령어로 Tool과 Agent import
* 개발 환경과 운영 환경 간 구성 재사용
* 기존 API 또는 Python 로직을 Agent에 연결

쉽게 말하면, **Agent Builder가 화면 중심의 제작 방식이라면 ADK는 개발자 중심의 확장 방식**입니다.

---

## 3. 사전 준비사항

실습 전 다음 항목이 준비되어 있어야 합니다.

| 항목                        | 설명                                     |
| ------------------------- | -------------------------------------- |
| VS Code                   | 코드 작성 및 터미널 실행용                        |
| Python 3.11 이상            | ADK 실행을 위한 Python 환경                   |
| watsonx Orchestrate 접속 정보 | Instance URL 또는 Service URL            |
| API Key                   | watsonx Orchestrate 환경 인증용             |
| 인터넷 연결                    | ADK 패키지 설치용                            |
| IBMid                     | watsonx Orchestrate 및 IBM Training 접속용 |

> 교육 환경에 따라 Instance URL, API Key는 강사가 별도로 안내할 수 있습니다.

---

## 4. VS Code 기본 설정

### 4.1 VS Code 실행

VS Code를 실행한 뒤, 작업용 폴더를 하나 생성합니다.

예시 폴더명:

```text
wxo-adk-demo
```

VS Code에서 다음 메뉴를 선택합니다.

```text
File > Open Folder > wxo-adk-demo 선택
```

---

### 4.2 VS Code 확장 설치

VS Code 왼쪽 메뉴에서 Extensions를 열고 다음 확장을 설치합니다.

```text
Python
```

선택 사항으로 아래 확장도 설치할 수 있습니다.

```text
IBM watsonx Orchestrate ADK
```

다만 이번 실습에서는 확장 기능보다 **VS Code 터미널에서 ADK CLI를 실행하는 방식**을 기준으로 진행합니다.

---

## 5. Python 가상환경 만들기

VS Code 상단 메뉴에서 터미널을 엽니다.

```text
Terminal > New Terminal
```

Windows PowerShell 기준으로 아래 명령어를 실행합니다.

```powershell
python --version
```

또는 Python Launcher가 설치되어 있다면 다음 명령어를 사용할 수 있습니다.

```powershell
py --version
```

Python 3.11 이상이 확인되면 가상환경을 생성합니다.

```powershell
py -3.11 -m venv .venv
```

가상환경을 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

만약 PowerShell 실행 정책 오류가 발생하면 아래 명령어를 먼저 실행합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

그 후 다시 가상환경을 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

정상적으로 활성화되면 터미널 앞에 `(.venv)`가 표시됩니다.

예시:

```powershell
(.venv) PS C:\workspace\wxo-adk-demo>
```

---

## 6. ADK 설치하기

가상환경이 활성화된 상태에서 pip를 업데이트합니다.

```powershell
python -m pip install --upgrade pip
```

watsonx Orchestrate ADK 패키지를 설치합니다.

```powershell
pip install --upgrade ibm-watsonx-orchestrate
```

설치가 완료되면 아래 명령어로 확인합니다.

```powershell
orchestrate --version
```

또는 다음 명령어를 실행합니다.

```powershell
orchestrate --help
```

정상적으로 도움말이 출력되면 ADK 설치가 완료된 것입니다.

---

## 7. watsonx Orchestrate 환경 연결하기

ADK CLI는 연결된 watsonx Orchestrate 환경을 대상으로 Tool과 Agent를 등록합니다.

먼저 강사에게 안내받은 값을 준비합니다.

```text
INSTANCE_URL=<강사가 제공한 watsonx Orchestrate URL>
API_KEY=<강사가 제공한 API Key>
```

환경을 등록합니다.

```powershell
orchestrate env add -n wxo-class -u <INSTANCE_URL> --type ibm_iam
```

등록한 환경을 활성화합니다.

```powershell
orchestrate env activate wxo-class --api-key <API_KEY>
```

환경 목록을 확인합니다.

```powershell
orchestrate env list
```

`wxo-class` 환경에 active 표시가 있으면 연결이 완료된 것입니다.

---

## 8. 첫 번째 Python Tool 만들기

VS Code에서 새 파일을 생성합니다.

```text
campaign_tool.py
```

아래 코드를 입력합니다.

```python
from ibm_watsonx_orchestrate.agent_builder.tools import tool


@tool()
def generate_campaign_message(product_name: str, target_audience: str, channel: str) -> str:
    """
    Generate a simple campaign message.

    Args:
        product_name: Product or service name.
        target_audience: Target audience for the campaign.
        channel: Marketing channel such as email, LinkedIn, or Instagram.

    Returns:
        Recommended campaign message.
    """
    return (
        f"{target_audience}를 대상으로 {channel} 채널에서 사용할 "
        f"{product_name} 캠페인 메시지입니다: "
        f"'지금 {product_name}으로 더 빠르고 스마트한 업무 경험을 시작하세요.'"
    )
```

이 코드는 마케팅 캠페인 문구를 생성하는 간단한 Tool입니다.

핵심은 `@tool()`입니다.
`@tool()`이 붙은 Python 함수는 watsonx Orchestrate에서 Agent가 사용할 수 있는 Tool로 등록할 수 있습니다.

---

## 9. Python Tool 등록하기

터미널에서 다음 명령어를 실행합니다.

```powershell
orchestrate tools import -k python -f campaign_tool.py
```

정상적으로 import되면 watsonx Orchestrate 환경에 Tool이 등록됩니다.

오류가 발생하면 debug 옵션을 붙여 확인합니다.

```powershell
orchestrate --debug tools import -k python -f campaign_tool.py
```

---

## 10. Agent YAML 파일 만들기

이번에는 Tool을 사용하는 간단한 Agent를 정의합니다.

VS Code에서 새 파일을 생성합니다.

```text
marketing_agent.yaml
```

아래 내용을 입력합니다.

```yaml
spec_version: v1
kind: native
name: Marketing_ADK_Demo_Agent
description: A simple marketing demo agent created with ADK
instructions: >
  You are a marketing assistant.
  Help users create short and clear campaign messages.
  When the user asks for a campaign message, use the available campaign tool if needed.
style: default
tools:
  - generate_campaign_message
collaborators: []
```

이 YAML 파일은 Agent의 이름, 설명, 지시문, 사용할 Tool을 정의합니다.

---

## 11. Agent 등록하기

터미널에서 다음 명령어를 실행합니다.

```powershell
orchestrate agents import -f marketing_agent.yaml
```

정상적으로 등록되면 watsonx Orchestrate에서 Agent를 확인할 수 있습니다.

Agent 목록을 확인하려면 다음 명령어를 실행합니다.

```powershell
orchestrate agents list
```

---

## 12. watsonx Orchestrate 화면에서 확인하기

브라우저에서 watsonx Orchestrate에 접속합니다.

확인 순서는 다음과 같습니다.

```text
1. watsonx Orchestrate 접속
2. Agent Builder 또는 Agent 관리 화면 이동
3. Marketing_ADK_Demo_Agent 확인
4. Tool 목록에서 generate_campaign_message 확인
5. Agent Preview 또는 Chat에서 테스트
```

테스트 질문 예시는 다음과 같습니다.

```text
20대 취준생을 대상으로 IBM watsonx Orchestrate 교육 홍보 문구를 만들어줘.
채널은 LinkedIn이야.
```

---

## 13. 수업용 데모 흐름

강사는 다음 순서로 데모를 진행할 수 있습니다.

```text
1. VS Code에서 프로젝트 폴더 열기
2. Python 가상환경 생성
3. ADK 설치
4. orchestrate --help 실행
5. watsonx Orchestrate 환경 연결
6. campaign_tool.py 작성
7. Tool import
8. marketing_agent.yaml 작성
9. Agent import
10. Orchestrate UI에서 Agent와 Tool 확인
```

이 데모를 통해 교육생은 다음 내용을 이해할 수 있습니다.

* ADK는 VS Code에서 실행할 수 있다.
* ADK는 Python 코드와 CLI를 사용한다.
* Python 함수는 Tool로 등록할 수 있다.
* YAML 파일로 Agent를 정의할 수 있다.
* 코드로 만든 Tool과 Agent를 watsonx Orchestrate UI에서 확인할 수 있다.

---

## 14. 자주 발생하는 오류

### 14.1 `orchestrate` 명령어를 찾을 수 없는 경우

가상환경이 활성화되어 있는지 확인합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

ADK가 설치되어 있는지 확인합니다.

```powershell
pip show ibm-watsonx-orchestrate
```

설치되어 있지 않다면 다시 설치합니다.

```powershell
pip install --upgrade ibm-watsonx-orchestrate
```

---

### 14.2 PowerShell 실행 정책 오류

아래 명령어를 실행합니다.

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

그 후 가상환경을 다시 활성화합니다.

```powershell
.\.venv\Scripts\Activate.ps1
```

---

### 14.3 환경 연결 오류

다음 항목을 확인합니다.

```text
1. Instance URL이 정확한가?
2. API Key가 정확한가?
3. API Key가 만료되지 않았는가?
4. 현재 네트워크에서 watsonx Orchestrate에 접속 가능한가?
5. env activate 명령어를 실행했는가?
```

환경 목록은 다음 명령어로 확인합니다.

```powershell
orchestrate env list
```

---

### 14.4 Tool import 오류

다음 항목을 확인합니다.

```text
1. 파일명이 정확한가?
2. @tool() 데코레이터가 있는가?
3. 함수의 입력값과 반환값에 타입 힌트가 있는가?
4. Python 문법 오류가 없는가?
5. 필요한 외부 패키지가 있다면 requirements.txt에 작성했는가?
```

debug 모드로 다시 실행합니다.

```powershell
orchestrate --debug tools import -k python -f campaign_tool.py
```

---

## 15. 정리

이번 실습에서는 VS Code에서 ADK를 사용하는 기본 흐름을 확인했습니다.

핵심 흐름은 다음과 같습니다.

```text
VS Code에서 코드 작성
  ↓
Python 가상환경 생성
  ↓
ADK 설치
  ↓
watsonx Orchestrate 환경 연결
  ↓
Python Tool 작성
  ↓
Tool import
  ↓
Agent YAML 작성
  ↓
Agent import
  ↓
Orchestrate UI에서 확인
```

ADK는 Agent Builder를 대체하는 도구가 아니라, Agent Builder로 만든 경험을 **개발자 방식으로 확장하는 도구**입니다.

실무에서는 다음과 같은 상황에서 ADK를 사용합니다.

| 상황                            | ADK 사용 이유                  |
| ----------------------------- | -------------------------- |
| 기존 Python 로직을 Agent에 연결해야 할 때 | Python Tool로 재사용 가능        |
| 외부 API를 Agent가 호출해야 할 때       | Tool과 Connection으로 연동 가능   |
| Agent 구성을 코드로 관리해야 할 때        | YAML/JSON/Python 파일로 관리 가능 |
| 여러 환경에 반복 배포해야 할 때            | CLI 기반으로 일관된 배포 가능         |
| 개발자와 현업이 함께 Agent를 운영해야 할 때   | 코드와 UI를 함께 활용 가능           |

따라서 ADK는 watsonx Orchestrate를 단순한 Agent 제작 도구에서 **기업 시스템과 연결 가능한 Agent 개발 플랫폼**으로 확장해 주는 역할을 합니다.
