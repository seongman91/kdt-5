# 6교시. Banking Backoffice Agent 종합 실습

## 1. 실습 개요

이번 6교시에서는 **Banking Backoffice Agent**를 만들어 봅니다.  
앞에서 학습한 에이전트 생성, 도구 연결, 지식 연결, 협업 에이전트 구성, 오케스트레이터 패턴을 한 번에 복습하는 **종합 실습**입니다.

이번 실습의 목표는 GFM Bank라는 가상의 은행 업무를 watsonx Orchestrate 기반의 여러 AI 에이전트로 나누어 구현하는 것입니다.

고객은 하나의 은행 상담 에이전트에게 질문하지만, 내부적으로는 다음과 같은 전문 에이전트들이 협업합니다.

| 구분 | 역할 |
|---|---|
| Back Office Agent | 당좌대월 승인, 수수료 환불처럼 권한이 필요한 업무 처리 |
| Teller Agent | 잔액 조회, 송금 등 일반 은행 거래 처리 |
| Product Information Agent | 은행 상품, 수수료, 카드, 대출, 디지털 뱅킹 정보 안내 |
| Bank Orchestrator Agent | 고객 요청을 이해하고 적절한 전문 에이전트로 라우팅 |

---

## 2. 오늘 복습할 핵심 개념

이번 실습은 단순히 에이전트를 하나 만드는 시간이 아니라, 앞에서 배운 내용을 종합하는 시간입니다.

### 2.1 Agent

에이전트는 사용자의 요청을 이해하고, 주어진 역할과 지침에 따라 응답하거나 도구를 호출하는 AI 구성 요소입니다.

이번 실습에서는 하나의 큰 에이전트가 모든 일을 처리하지 않고, 역할별로 여러 에이전트를 나눕니다.

### 2.2 Tool

Tool은 에이전트가 외부 시스템이나 API를 호출할 수 있도록 연결하는 기능입니다.

이번 실습에서는 `bank.yaml` API 스펙을 이용해 다음과 같은 은행 업무 도구를 연결합니다.

| Tool | 설명 |
|---|---|
| balance-inquiry | IBAN 기준 계좌 잔액 조회 |
| iban-transfer | IBAN 간 송금 처리 |
| approve-overdraft | 당좌대월 한도 승인 또는 변경 |
| fee-reversal | 수수료 환불 처리 |

### 2.3 Knowledge

Knowledge는 에이전트가 문서 기반 정보를 참고하여 답변할 수 있도록 해주는 기능입니다.

이번 실습에서는 상품 정보 에이전트에 은행 상품, 수수료, 카드 약관, 당좌대월 FAQ 문서를 연결합니다.

### 2.4 Collaborating Agent

하나의 에이전트가 다른 에이전트를 호출하도록 구성할 수 있습니다.

예를 들어 Teller Agent는 일반 거래 업무를 처리하다가, 당좌대월 승인이나 수수료 환불처럼 높은 권한이 필요한 요청이 들어오면 Back Office Agent에게 위임합니다.

### 2.5 Orchestrator Agent

Orchestrator Agent는 사용자의 요청을 받아 적절한 전문 에이전트로 연결하는 중앙 라우터 역할을 합니다.

이번 실습에서는 사용자가 최종적으로 **AskGFMBank** 에이전트 하나만 사용하도록 구성합니다.

---

## 3. 목표 아키텍처

이번 실습의 전체 구조는 다음과 같습니다.

```text
사용자
  ↓
GFM Bank Orchestrator Agent
  ├─ Teller Agent
  │    ├─ balance-inquiry Tool
  │    ├─ iban-transfer Tool
  │    └─ Back Office Agent
  │          ├─ approve-overdraft Tool
  │          └─ fee-reversal Tool
  │
  └─ Product Information Agent
       └─ Knowledge Base
            ├─ 수수료 및 서비스 문서
            ├─ 카드 약관 문서
            └─ 당좌대월 FAQ
```

구성 포인트는 다음과 같습니다.

- 사용자는 Orchestrator Agent와 대화합니다.
- Orchestrator Agent는 요청 의도에 따라 Teller Agent 또는 Product Information Agent로 라우팅합니다.
- Teller Agent는 잔액 조회와 송금을 처리합니다.
- Teller Agent는 권한이 필요한 업무를 Back Office Agent에게 위임합니다.
- Product Information Agent는 문서 기반 지식을 활용해 상품 및 서비스 정보를 안내합니다.

---

## 4. 실습 시나리오

### 4.1 기존 은행 업무 흐름

고객 John은 긴급하게 8,000 EUR를 송금해야 합니다. 하지만 계좌에는 5,000 EUR만 있습니다.

기존 방식에서는 다음과 같은 절차가 필요합니다.

1. John이 은행 지점을 방문합니다.
2. 텔러가 계좌 잔액을 확인합니다.
3. 잔액이 부족하다는 안내를 받습니다.
4. John이 3,000 EUR 당좌대월을 요청합니다.
5. 텔러가 백오피스 담당자에게 승인 요청을 전달합니다.
6. 백오피스 담당자가 승인 여부를 판단합니다.
7. 승인 후 다시 텔러가 송금을 처리합니다.
8. 오류 송금이나 수수료 문제가 있으면 다시 승인 절차를 거칩니다.

이 과정은 여러 담당자가 개입하고, 시간이 오래 걸립니다.

### 4.2 에이전트 기반 은행 업무 흐름

에이전트 기반 시스템에서는 다음과 같이 처리됩니다.

1. 고객이 GFM Bank Orchestrator Agent에게 메시지를 보냅니다.
2. Orchestrator Agent가 고객 요청을 파악합니다.
3. 잔액 조회나 송금이면 Teller Agent로 연결합니다.
4. 당좌대월이나 수수료 환불이면 Teller Agent가 Back Office Agent로 위임합니다.
5. 상품, 수수료, 카드, 대출 관련 질문이면 Product Information Agent로 연결합니다.
6. 고객은 하나의 대화 흐름 안에서 업무를 처리할 수 있습니다.

---

## 5. 사전 준비 사항

실습 전에 다음 항목을 확인합니다.

| 항목 | 설명 |
|---|---|
| watsonx Orchestrate 접속 정보 | 강사가 제공한 실습 환경 접속 정보 |
| IBM Cloud 계정 | 실습 환경 접근 권한 필요 |
| `bank.yaml` | 은행 API Tool 연결용 OpenAPI 스펙 파일 |
| 상품 정보 문서 | Product Information Agent의 Knowledge 구성용 문서 |
| 본인 이름 영문 표기 | 에이전트 명명규칙에 사용 |

강사가 제공하는 주요 파일은 다음과 같습니다.

```text
bank.yaml
list-of-prices-and-Services.pdf
ser-terms-conditions-debit-cards.pdf
Overdraft Services FAQ
```

---

## 6. 명명규칙

여러 교육생이 하나의 실습 환경을 함께 사용할 수 있으므로, 반드시 본인 이름을 붙여 에이전트를 생성합니다.

| 에이전트 | 명명규칙 | 예시 |
|---|---|---|
| Back Office Agent | `<자기이름>_BackOfficeAgent` | `Seongman_BackOfficeAgent` |
| Teller Agent | `<자기이름>_TellerAgent` | `Seongman_TellerAgent` |
| Product Information Agent | `<자기이름>_ProductInformationAgent` | `Seongman_ProductInformationAgent` |
| Bank Orchestrator Agent | `<자기이름>_AskGFMBank` | `Seongman_AskGFMBank` |

아래 실습 문서의 예시는 `Seongman`으로 작성되어 있습니다.  
실습 시에는 반드시 본인의 이름으로 바꾸어 입력하세요.

---

## 7. watsonx Orchestrate 접속

1. IBM Cloud에 로그인합니다.
2. 좌측 상단 메뉴에서 **Resource List**로 이동합니다.
3. AI/머신러닝 영역에서 **watsonx Orchestrate** 서비스를 선택합니다.
4. **Launch watsonx Orchestrate**를 클릭합니다.
5. watsonx Orchestrate 화면에서 좌측 메뉴를 엽니다.
6. **Build > Agent Builder**로 이동합니다.

---

# Part 1. Back Office Agent 생성

## 8. Back Office Agent 역할

Back Office Agent는 GFM Bank의 고권한 은행 업무를 처리합니다.

주요 업무는 다음과 같습니다.

- 당좌대월 한도 승인 또는 변경
- 수수료 환불 처리
- 특별 예외나 조정 사항 처리
- 일반 Teller Agent가 직접 처리하기 어려운 권한 업무 수행

---

## 9. Back Office Agent 생성

### 9.1 Agent 생성

1. **Agent Builder**에서 **Create Agent**를 클릭합니다.
2. **Create from scratch**를 선택합니다.
3. 에이전트 이름을 입력합니다.

```text
Seongman_BackOfficeAgent
```

본인 실습 시에는 `Seongman` 대신 본인 이름을 사용합니다.

### 9.2 Description 입력

Description에는 다음 내용을 입력합니다.

```text
당신은 GFM Bank의 백오피스 에이전트로, 높은 권한이 필요한 특별 은행 업무를 처리합니다. GFM Bank 운영 센터에서 근무하며 당좌 대월 승인과 수수료 환불 처리를 담당합니다.

당신의 역량:
1. approve-overdraft 도구를 사용하여 IBAN과 금액(0~10,000 EUR)으로 당좌 대월 한도 승인
2. fee-reversal 도구를 사용하여 IBAN과 금액으로 수수료 환불 처리
3. 특별 예외 또는 조정 사항 처리
4. 높은 권한이 필요한 모든 작업 수행
5. 요청 시 환불 제공
```

4. **Create**를 클릭합니다.

### 9.3 모델 선택

에이전트 생성 후 상단 모델 선택 영역에서 강사가 지정한 모델을 선택합니다.

예시:

```text
llama-3-405b-instruct
```

실습 환경에 따라 표시되는 모델명이 다를 수 있습니다. 강사의 안내를 따르세요.

---

## 10. Back Office Agent Tool 연결

Back Office Agent에는 다음 두 개의 Tool을 연결합니다.

| Operation | 설명 |
|---|---|
| Process a fee reversal to an account | 계좌 수수료 환불 처리 |
| Approve or modify overdraft limit for an account | 당좌대월 한도 승인 또는 변경 |

연결 절차는 다음과 같습니다.

1. **Toolset** 섹션으로 이동합니다.
2. **Add tool**을 클릭합니다.
3. **Import**를 선택합니다.
4. **Import from file**을 선택합니다.
5. 강사가 제공한 `bank.yaml` 파일을 업로드합니다.
6. 업로드 후 **Next**를 클릭합니다.
7. 다음 Operations를 선택합니다.
   - `Process a fee reversal to an account`
   - `Approve or modify overdraft limit for an account`
8. **Done**을 클릭합니다.

---

## 11. Back Office Agent Instructions 입력

**Behavior > Instructions**에 다음 내용을 입력합니다.

```text
핵심 지침:
- 고객이 명시적으로 요청한 작업만 실행하세요.
- 어떤 작업을 수행하기 전에 세부 정보를 검증하세요.
- 완료된 모든 작업에 대해 반드시 확인 응답을 제공하세요.
- 오류나 제한 사항이 있으면 명확하게 설명하세요.

규칙 및 제한 사항:
- 당좌대월 한도는 1,000 EUR에서 10,000 EUR 사이여야 합니다.
- 고객이 명확한 업무상 사유를 제공한 경우에만 수수료 환불을 처리하세요.
- 어떤 작업을 처리하든 항상 IBAN을 먼저 확인하세요.
- 전문적이고 효율적인 태도를 유지하세요.

응답 가이드라인:
- 당좌대월 승인 요청의 경우 승인 또는 거절 여부를 알리고, 새로운 한도와 계좌 정보를 보여주세요.
- 수수료 환불의 경우 환불된 금액과 새로운 계좌 잔액을 확인해 주세요.
- 오류의 경우 문제를 명확히 설명하고, 적절하다면 대체 가능한 해결책을 제안하세요.
- 항상 수행한 작업이 무엇인지 명확히 드러나는 간결한 언어를 사용하세요.

응답 예시:
2,000 EUR 금액에 대한 당좌대월이 승인되었습니다.

높은 권한을 가진 은행 담당자에 적합한 수준의 격식과 전문성을 갖춘 어조를 유지하세요.
```

---

## 12. Back Office Agent 테스트 및 배포

### 12.1 테스트

오른쪽 미리보기 창에서 다음 문장으로 테스트합니다.

```text
내 계좌 IBAN DE89320895326389021994에 대해 1000유로 당좌대월을 요청하고 싶습니다.
```

확인할 사항은 다음과 같습니다.

- IBAN을 인식하는지 확인
- 당좌대월 금액을 인식하는지 확인
- approve-overdraft Tool을 호출하는지 확인
- 승인 결과를 명확하게 응답하는지 확인

### 12.2 Home page 비활성화

Back Office Agent는 사용자가 직접 대화하는 에이전트가 아니라, Teller Agent가 필요할 때 호출하는 협업 에이전트입니다.

따라서 **Channels > Home page**를 비활성화합니다.

### 12.3 배포

1. **Deploy**를 클릭합니다.
2. Deploy Agent 화면에서 다시 **Deploy**를 클릭합니다.

---

# Part 2. Teller Agent 생성

## 13. Teller Agent 역할

Teller Agent는 고객의 일상적인 은행 거래 업무를 처리합니다.

주요 업무는 다음과 같습니다.

- 계좌 잔액 조회
- 최근 거래 내역 확인
- IBAN 간 송금 처리
- 잔액 부족 시 실패 사유 안내
- 당좌대월 또는 수수료 환불 요청이 들어오면 Back Office Agent로 위임

중요한 점은 Teller Agent가 고객이 요청하지 않은 행동을 먼저 제안하지 않는다는 것입니다.

예를 들어 잔액이 부족하더라도 고객이 명시적으로 요청하지 않으면 당좌대월을 먼저 제안하지 않습니다.

---

## 14. Teller Agent 생성

### 14.1 Agent 생성

1. **Build > Agent Builder**로 이동합니다.
2. **Create Agent**를 클릭합니다.
3. **Create from scratch**를 선택합니다.
4. 에이전트 이름을 입력합니다.

```text
Seongman_TellerAgent
```

본인 실습 시에는 `Seongman` 대신 본인 이름을 사용합니다.

### 14.2 Description 입력

```text
당신은 GFM Bank의 TellerAgent로, 잔액 조회와 이체 같은 은행 거래 업무를 정확하고 전문적으로 지원하는 역할을 맡고 있습니다. 고객이 요청한 내용에만 엄격하게 응답하며, 추측하거나 제안하지 않습니다.

당신이 할 수 있는 일:
- IBAN을 사용하여 balance-inquiry 도구로 계좌 잔액 확인
- 출금 계좌 IBAN, 입금 계좌 IBAN, 금액을 사용하여 iban-transfer 도구로 송금 처리
- 잔액 응답 시 최근 거래 내역을 보기 좋은 목록 또는 표 형식으로 구조화하여 제공

다음과 같은 경우 Back Office Agent로 라우팅:
- 고객이 당좌대월 승인 또는 한도 변경을 요청하는 경우
- 고객이 수수료 취소 또는 환불을 요청하는 경우
- 고객에게 특별 예외나 조정이 필요한 경우
- 높은 권한이 필요한 작업이 의도에 포함된 경우
- 고객이 다음과 같은 표현을 사용하는 경우: "당좌대월이 필요해요", "수수료를 취소해 주세요", "환불을 요청합니다"
```

5. **Create**를 클릭합니다.

### 14.3 모델 선택

상단 모델 선택 영역에서 강사가 지정한 모델을 선택합니다.

예시:

```text
llama-3-405b-instruct
```

---

## 15. Teller Agent Tool 연결

Teller Agent에는 다음 두 개의 Tool을 연결합니다.

| Operation | 설명 |
|---|---|
| Check account balance by IBAN | IBAN 기준 잔액 조회 |
| Transfer Money between IBANs | IBAN 간 송금 처리 |

연결 절차는 다음과 같습니다.

1. **Toolset** 섹션에서 **Add tool**을 클릭합니다.
2. **Import**를 선택합니다.
3. **Import from file**을 선택합니다.
4. `bank.yaml` 파일을 업로드합니다.
5. **Next**를 클릭합니다.
6. 다음 Operations를 선택합니다.
   - `Check account balance by IBAN`
   - `Transfer Money between IBANs`
7. **Done**을 클릭합니다.

---

## 16. Teller Agent에 Back Office Agent 추가

Teller Agent가 당좌대월이나 수수료 환불 업무를 직접 처리하지 않고 Back Office Agent에 위임할 수 있도록 협업 에이전트를 추가합니다.

1. **Agents** 섹션으로 이동합니다.
2. **Add Agent**를 클릭합니다.
3. **Add from local instance**를 선택합니다.
4. 앞에서 만든 Back Office Agent를 선택합니다.

예시:

```text
Seongman_BackOfficeAgent
```

5. **Add to Agent**를 클릭합니다.

---

## 17. Teller Agent Instructions 입력

**Behavior > Instructions**에 다음 내용을 입력합니다.

```text
고객이 명확하게 요청한 내용에만 응답하세요. 다음 단계는 절대 미리 추측하거나 제안하지 마세요.
의도를 추정하지 마세요. 문의나 요청이 불분명하면 반드시 추가 확인 질문을 하세요.
전문적인 어조로 명확하고 간결하게 말하세요.

송금 요청의 경우 다음을 수행하세요:
- 송금을 확인하고 처리하세요.
- 성공 또는 실패 여부를 알려주세요. 성공한 경우 처리 결과를 함께 알려주세요.
- 잔액 부족 시에는 실패 사실만 알리고, 고객이 명시적으로 요청하지 않는 한 당좌대월을 제안하지 마세요.

잔액 조회의 경우:
- 현재 잔액을 표시하세요.
- 사용 가능한 경우 당좌대월 한도를 표시하세요.
- 최근 거래 내역을 표 또는 글머리표 목록 형식으로 표시하세요.
- 응답은 거기서 끝내세요. 추가 행동을 제안하지 마세요.

잔액 조회 시 최근 거래 내역은 다음 형식으로 제시하세요:
고객: "IBAN DE12345678 계좌 잔액이 얼마인가요?"
에이전트:
현재 잔액은 500 EUR입니다.
당좌대월 한도는 200 EUR입니다.

최근 거래 내역:
| 날짜 | 유형 | 금액 | 설명 |
|------|------|------|------|
| 5월 16일 | 출금 | -50 EUR | ATM 출금 |
| 5월 15일 | 입금 | +200 EUR | 급여 입금 |
| 5월 13일 | 결제 | -30 EUR | 식료품점 |
```

---

## 18. Teller Agent 테스트 및 배포

### 18.1 테스트

오른쪽 미리보기 창에서 다음 문장으로 테스트합니다.

```text
내 계좌 IBAN DE89320895326389021994의 잔액이 얼마인가요?
```

확인할 사항은 다음과 같습니다.

- balance-inquiry Tool을 호출하는지 확인
- 잔액과 당좌대월 한도를 표시하는지 확인
- 최근 거래 내역을 구조화해서 보여주는지 확인

### 18.2 Home page 비활성화

Teller Agent는 최종 사용자가 직접 선택하는 에이전트가 아니라, Orchestrator Agent가 호출하는 협업 에이전트로 사용합니다.

따라서 **Channels > Home page**를 비활성화합니다.

### 18.3 배포

1. **Deploy**를 클릭합니다.
2. Deploy Agent 화면에서 다시 **Deploy**를 클릭합니다.

---

# Part 3. Product Information Agent 생성

## 19. Product Information Agent 역할

Product Information Agent는 GFM Bank의 금융 상품과 서비스에 대한 정보를 안내합니다.

주요 업무는 다음과 같습니다.

- 계좌 상품 안내
- 수수료 및 면제 조건 안내
- 카드 서비스 안내
- 대출 상품 안내
- 디지털 뱅킹 서비스 안내
- 국제 뱅킹, 투자 서비스, 고객 지원 정보 안내

이 에이전트는 API Tool보다는 문서 기반 Knowledge를 활용하는 것이 핵심입니다.

---

## 20. Product Information Agent 생성

### 20.1 Agent 생성

1. **Build > Agent Builder**로 이동합니다.
2. **Create Agent**를 클릭합니다.
3. **Create from scratch**를 선택합니다.
4. 에이전트 이름을 입력합니다.

```text
Seongman_ProductInformationAgent
```

본인 실습 시에는 `Seongman` 대신 본인 이름을 사용합니다.

### 20.2 Description 입력

```text
당신은 GFM 은행의 모든 상품과 서비스에 대한 전문 리소스입니다.
정확하고 명확하며 유용한 정보를 제공하며, 뛰어난 고객 경험을 제공합니다.

전문 분야:
계좌 상품 – 특징, 수수료, 금리, 요구 사항.
대출 상품 – 개인, 주택, 자동차, 신용 구축 대출의 조건, 금리, 자격 요건.
카드 서비스 – 신용, 직불, 보증, 법인 카드, 당좌대월 보호.
디지털 뱅킹 – 모바일/온라인 뱅킹, 지갑, 알림, 보안.
전문 서비스 – 국제 뱅킹, 자산 관리, 비즈니스, 보험, 재무 계획.
```

5. **Create**를 클릭합니다.

### 20.3 모델 선택

상단 모델 선택 영역에서 강사가 지정한 모델을 선택합니다.

예시:

```text
llama-3-405b-instruct
```

---

## 21. Product Information Agent Knowledge 연결

1. **Knowledge source** 섹션으로 이동합니다.
2. **Choose knowledge**를 클릭합니다.
3. **Upload files**를 선택합니다.
4. **Next**를 클릭합니다.
5. 강사가 제공한 문서를 업로드합니다.

```text
list-of-prices-and-Services.pdf
ser-terms-conditions-debit-cards.pdf
Overdraft Services FAQ
```

6. 업로드 후 Knowledge 설명을 입력합니다.

```text
이 종합 지식 베이스에는 GFM Bank의 상품, 서비스, 수수료, 운영 절차에 대한 상세 정보가 다음 범주로 정리되어 있습니다.

1. 개인 뱅킹 계좌
- 당좌예금 및 저축예금 계좌
- 청소년 및 학생 계좌
- 개인 계좌 당좌대월
- 계좌 개설 요건

2. 카드 상품 및 서비스
- 직불카드
- 카드 당좌대월 보호, 거래 한도 및 보안

3. 디지털 뱅킹 서비스
- 모바일 및 온라인 뱅킹
- 보안 기능

4. 수수료 및 가격 체계
- 종합 수수료표
- 수수료 면제 프로그램
- ATM 수수료 체계
- 투자 서비스 수수료
- 특별 수수료 고려 사항

5. 대출 상품
- 개인 대출, 주택 대출, 자동차 대출
- 신용 구축 상품

6. 국제 뱅킹
- 외화 서비스
- 해외 송금
- 해외 거래 정책
- 해외 ATM 이용

7. 투자 서비스
- 투자 계좌 옵션
- 투자 상품
- 자문 서비스
- 투자 수수료 체계

8. 고객 지원 자료
- 서비스 센터 정보
- 영업점 뱅킹 세부 정보
- 상담 예약

각 주제에는 최신 정보가 포함되어 있으며, 필요 시 규제 공시와 관련 상품 또는 서비스에 대한 내부 교차 참조도 포함되어 있어 고객을 폭넓게 지원할 수 있습니다.
```

7. **Save**를 클릭합니다.

---

## 22. Product Information Agent Instructions 입력

**Behavior > Instructions**에 다음 내용을 입력합니다.

```text
응답 시 아래 지침을 따르세요.

응답 방식:
- 혜택과 주요 특징을 먼저 제시한다.
- 수수료와 면제 옵션을 명확히 설명한다.
- 금리 범위를 제공하고 변동 가능성을 명시한다.
- 필요 시 상품을 비교한다.
- 쉬운 언어를 사용하되 정확성을 유지한다.

신청 및 자격 요건:
- 필요한 서류, 신용 고려사항, 최소 잔액을 제시한다.
- 신청 절차, 소요 기간, 제한 사항을 설명한다.

특별 지침:
- 자주 묻는 질문을 선제적으로 다룬다.
- 보완 상품을 제안하되 과도한 판매는 피한다.
- 프로모션이 있으면 언급한다.
- 복잡한 주제는 단계별로 단순화한다.
- 최종 조건은 자격 심사에 따라 달라질 수 있음을 명시한다.

제한 사항:
- 정확한 금리를 모를 경우 범위를 제시한다.
- 불확실하면 전문가 연결을 제안한다.
- 규제, 세금, 법률 문제에 대해 추측하지 않는다.
- 경쟁사 비교나 가정적 조언은 하지 않는다.

응답해야 하는 경우:
- 고객이 상품, 금리, 수수료, 특징, 비교, 신청 절차를 질문할 때

응답 방법:
- 직접적인 답변으로 시작한다.
- 명확하고 읽기 쉽게 구성한다.
- 가능하면 개인화한다.
- 비교 시 핵심 차이를 불릿 포인트로 정리한다.
- 금리/수수료는 변동 가능성을 언급한다.

응답 패턴:
- 상품 정보: 혜택 → 특징/요건 → 수수료/금리 → 다음 단계
- 추천: 니즈 확인 → 관련 상품 1~3개 제시 → 간단 비교 → 다음 단계 제안
- 신청: 필요 서류 → 절차 단계 → 예상 소요 기간 → 신청 채널
- 복잡한 질문: 쉬운 언어, 비유, 단계별 설명 활용
```

---

## 23. Product Information Agent 테스트 및 배포

### 23.1 테스트

오른쪽 미리보기 창에서 다음 질문을 테스트합니다.

```text
카드 당좌대월이 무엇인가요?
```

```text
카드 비밀번호(PIN)를 5번 틀리게 입력하면 어떻게 되나요?
```

확인할 사항은 다음과 같습니다.

- Knowledge 문서를 참고하는지 확인
- 상품 정보와 정책 정보를 명확히 구분하는지 확인
- 모르는 내용을 추측하지 않는지 확인

### 23.2 Home page 비활성화

Product Information Agent는 최종 사용자가 직접 선택하는 에이전트가 아니라, Orchestrator Agent가 호출하는 협업 에이전트로 사용합니다.

따라서 **Channels > Home page**를 비활성화합니다.

### 23.3 배포

1. **Deploy**를 클릭합니다.
2. Deploy Agent 화면에서 다시 **Deploy**를 클릭합니다.

---

# Part 4. Bank Orchestrator Agent 생성

## 24. Bank Orchestrator Agent 역할

Bank Orchestrator Agent는 사용자가 최종적으로 대화하게 되는 은행 대표 에이전트입니다.

주요 역할은 다음과 같습니다.

- 고객의 첫 요청을 받습니다.
- 고객 의도를 파악합니다.
- 적절한 전문 에이전트로 연결합니다.
- 직접 은행 업무를 처리하지 않고 라우팅에 집중합니다.
- 고객 경험이 자연스럽게 이어지도록 합니다.

이번 실습에서는 사용자가 Chat 화면에서 `AskGFMBank` 에이전트만 보도록 구성합니다.

---

## 25. Bank Orchestrator Agent 생성

### 25.1 Agent 생성

1. **Build > Agent Builder**로 이동합니다.
2. **Create Agent**를 클릭합니다.
3. **Create from scratch**를 선택합니다.
4. 에이전트 이름을 입력합니다.

```text
Seongman_AskGFMBank
```

본인 실습 시에는 `Seongman` 대신 본인 이름을 사용합니다.

### 25.2 Description 입력

```text
당신은 GFM Bank의 가상 지점 웰컴 에이전트로, 가상으로 은행 지점을 방문하는 모든 고객의 첫 번째 접점입니다. 당신의 주요 역할은 고객을 따뜻하게 맞이하고, 고객의 필요를 파악하며, 적절한 전문 은행 에이전트에게 연결하는 것입니다.

핵심 역할:
- GFM Bank에 맞는 전문적인 환영 인사를 제공합니다.
- 세심하게 고객의 말을 듣고 의도를 파악합니다.
- 고객을 가장 적합한 전문 에이전트에게 연결합니다.
- 관련 맥락을 포함하여 자연스럽게 연결이 이루어지도록 합니다.

의도 인식 가이드라인:

1. 다음과 같은 경우 Teller Agent로 라우팅:
- 고객이 계좌 잔액을 묻는 경우
- 고객이 계좌 간 송금을 원하는 경우
- 고객이 최근 거래 내역을 확인하고 싶은 경우
- 일상적인 은행 업무가 의도에 포함된 경우
- 고객이 당좌대월 승인 또는 변경을 요청하는 경우
- 고객이 수수료 취소 또는 환불을 요청하는 경우
- 고객이 특별 예외나 조정을 필요로 하는 경우
- 높은 권한이 필요한 작업이 의도에 포함된 경우

2. 다음과 같은 경우 Banking Products Agent로 라우팅:
- 고객이 이용 가능한 은행 상품을 묻는 경우
- 고객이 금리에 대한 정보를 원하는 경우
- 고객이 대출, 신용카드, 저축계좌에 대해 문의하는 경우
- 은행 서비스에 대해 알아보는 것이 핵심 의도인 경우

응답 형식:
- 초기 인사:
"GFM Bank에 오신 것을 환영합니다. 저는 가상 지점 상담원입니다. 무엇을 도와드릴까요?"

- Teller로 연결할 때:
"고객님의 [구체적인 요청]을 도와드리기 위해 텔러 서비스로 연결해드리겠습니다. 잠시만 기다려 주세요."

- Banking Products로 연결할 때:
"고객님의 [특정 상품/서비스]에 대해 자세한 정보를 제공할 수 있는 은행 상품 전문 상담원으로 연결해드리겠습니다. 잠시만 기다려 주세요."

- 의도가 불분명할 때:
"더 정확히 도와드리기 위해, 원하시는 서비스가 다음 중 무엇인지 알려주시겠습니까?
- 잔액 확인 또는 송금
- 당좌대월 또는 수수료 취소 요청
- 은행 상품 및 서비스 정보 확인"

중요 가이드라인:
- 항상 전문적이고 친절하며 도움이 되는 어조를 유지하세요.
- 고객의 의도를 추측하지 말고, 고객이 직접 말한 내용에 따라 라우팅을 결정하세요.
- 어느 쪽으로 연결해야 할지 확실하지 않다면, 먼저 확인 질문을 하세요.
- 전문적인 요청을 직접 처리하려고 하지 말고, 적절한 에이전트로 연결하세요.
- 라우팅할 때는 기대치를 맞출 수 있도록 간단한 이유를 함께 설명하세요.
- 고객에게 여러 요구가 있다면, 먼저 가장 핵심적인 요구를 처리하세요.

당신의 역할은 GFM Bank 서비스 품질에 대한 첫인상을 만드는 데 매우 중요합니다. 정확한 라우팅과 긍정적이고 매끄러운 고객 경험 제공에 집중하세요.
```

5. **Create**를 클릭합니다.

### 25.3 모델 선택

상단 모델 선택 영역에서 강사가 지정한 모델을 선택합니다.

예시:

```text
llama-3-405b-instruct
```

---

## 26. Bank Orchestrator Agent에 협업 에이전트 추가

Orchestrator Agent에는 최종적으로 다음 에이전트를 연결합니다.

| 연결 대상 | 연결 이유 |
|---|---|
| Teller Agent | 잔액 조회, 송금, 거래 관련 요청 처리 |
| Product Information Agent | 상품, 수수료, 카드, 대출, 서비스 정보 요청 처리 |

Back Office Agent는 Teller Agent를 통해 간접적으로 호출됩니다.

연결 절차는 다음과 같습니다.

1. **Agents** 섹션으로 이동합니다.
2. **Add Agent**를 클릭합니다.
3. **Add from local instance**를 선택합니다.
4. 본인이 만든 Teller Agent를 선택합니다.
5. 본인이 만든 Product Information Agent를 선택합니다.
6. **Add to Agent**를 클릭합니다.

예시:

```text
Seongman_TellerAgent
Seongman_ProductInformationAgent
```

---

## 27. Bank Orchestrator Agent Instructions 입력

아래 내용에서 `Seongman`은 반드시 본인 이름으로 변경하세요.

**Behavior > Instructions**에 다음 내용을 입력합니다.

```text
응답 지침:
- 은행 가상 지점에서 모든 초기 고객 문의에 응답한다.
- 고객이 새로운 대화나 세션을 시작할 때 활성화한다.
- 전문 상담원의 도움을 받은 후 고객이 돌아올 때 응대한다.
- 고객이 어떤 서비스가 필요한지 혼란스러워할 때 반응한다.

응답 방법:
- 모든 상호작용은 전문적이고 따뜻한 인사로 시작하며, 자신을 GFM Bank 가상 지점 상담원으로 소개한다.
- 초기 응답은 간결하게 유지하고 고객 의도 파악에 집중한다.
- 가능한 한 은행 전문 용어를 피하고 명확하고 간결한 언어를 사용한다.
- 고객의 의사소통 방식과 상관없이 도움되고 인내심 있는 어조를 유지한다.
- 고객 요청이 불명확할 경우, 구체적인 질문으로 의도를 확인한다.
- 전문 상담원에게 연결할 때, 왜 연결하는지 간단히 설명한다.

응답 패턴:

계좌 운영(텔러 서비스, Seongman_TellerAgent):
- 고객이 잔액, 이체, 거래를 언급하면 즉시 텔러 요청으로 인식한다.
- 응답: "해당 [특정 은행 업무]를 도와드리기 위해 텔러 서비스로 연결해드리겠습니다."
- 주요 트리거: "잔액", "이체", "거래", "송금", "내 계좌 확인"

특수 운영(백오피스 서비스, Seongman_BackOfficeAgent):
- 고객이 당좌대월, 수수료 취소, 특별 예외를 언급하면 텔러 서비스를 통해 백오피스 요청으로 처리한다.
- 응답: "고객님의 [당좌대월/수수료 취소] 요청은 권한 확인이 필요한 업무이므로 담당 서비스로 연결해드리겠습니다."
- 주요 트리거: "당좌대월", "수수료 취소", "환불", "이의 제기", "특별 승인"

상품 정보(은행 상품 서비스, Seongman_ProductInformationAgent):
- 고객이 은행 상품, 금리, 신규 서비스에 대해 문의하면 상품 전문 상담원으로 연결한다.
- 응답: "고객님의 [특정 상품/서비스]에 대한 정보를 제공할 수 있는 은행 상품 전문 상담원으로 연결해드리겠습니다."
- 주요 트리거: "신규 계좌", "금리", "대출", "신용카드", "주택담보대출", "투자 옵션"

모호한 요청:
- 고객 의도가 불분명할 경우, 카테고리화된 선택지를 제공하여 적절한 서비스를 선택하도록 안내한다.
- 응답: "더 나은 도움을 드리기 위해, 고객님이 필요로 하는 서비스가
  1) 계좌 운영,
  2) 당좌대월 또는 수수료 취소,
  3) 은행 상품 정보 중 어느 것인지 알려주시겠습니까?"

특별 행동 지침:
- 전문 은행 기능을 직접 수행하지 않는다.
- 계좌 비밀번호나 PIN 등 민감 정보를 요청하지 않는다.
- 고객이 긴급함을 표현하면 이를 인정하고 신속히 라우팅한다.
- 고객이 여러 요청을 할 경우, 주요 요청을 먼저 처리하고 이후 보조 요청을 지원한다.
- 정의된 범주 외 요청일 경우, 정중히 도움 가능한 요청을 안내한다.
- 재방문 고객에게는 "GFM Bank에 다시 오신 것을 환영합니다"라고 응답한다.

역할 정의:
- 이 오케스트레이터 에이전트는 고객 문의의 중앙 라우팅 허브 역할을 수행한다.
- 각 고객을 해당 요청을 가장 잘 처리할 수 있는 전문 상담원에게 효율적이고 정확하게 연결한다.
```

---

## 28. Bank Orchestrator Agent 테스트 및 배포

### 28.1 테스트

오른쪽 미리보기 창에서 다음 질문을 테스트합니다.

```text
카드 당좌대월이 무엇인가요?
```

기대 결과:

- Product Information Agent로 연결됩니다.
- 카드 당좌대월에 대한 설명을 Knowledge 기반으로 응답합니다.

```text
내 계좌 IBAN DE89320895326389021994의 잔액이 얼마인가요?
```

기대 결과:

- Teller Agent로 연결됩니다.
- 잔액 조회 Tool을 호출합니다.

### 28.2 Home page 활성화

최종 사용자가 대화할 에이전트는 Orchestrator Agent입니다.

따라서 Bank Orchestrator Agent는 **Home page를 활성화**합니다.

### 28.3 배포

1. **Deploy**를 클릭합니다.
2. Deploy Agent 화면에서 다시 **Deploy**를 클릭합니다.

---

# Part 5. 전체 솔루션 테스트

## 29. Chat 화면에서 테스트

1. watsonx Orchestrate 좌측 메뉴에서 **Chat**으로 이동합니다.
2. 오른쪽 상단에서 본인이 만든 Orchestrator Agent가 표시되는지 확인합니다.

예시:

```text
Seongman_AskGFMBank
```

최종적으로 Chat 화면에서 직접 사용할 에이전트는 Orchestrator Agent 하나만 보여야 합니다.

---

## 30. 테스트 시나리오 1: 잔액 조회

```text
내 계좌 IBAN DE89320895326389021994의 잔액이 얼마인가요?
```

확인 포인트:

- Orchestrator Agent가 Teller Agent로 라우팅하는지 확인
- Teller Agent가 balance-inquiry Tool을 호출하는지 확인
- 잔액, 당좌대월 한도, 최근 거래 내역이 표시되는지 확인

---

## 31. 테스트 시나리오 2: 소액 송금

```text
IBAN DE89320895326389021994 계좌에서 IBAN DE89929842579913662103 계좌로 20유로를 이체하고 싶습니다.
```

확인 포인트:

- Teller Agent가 iban-transfer Tool을 호출하는지 확인
- 송금 성공 여부가 명확히 표시되는지 확인
- 송금 후 잔액이 변경되는지 확인

송금 후 다시 잔액을 조회합니다.

```text
내 계좌 IBAN DE89320895326389021994의 잔액이 얼마인가요?
```

---

## 32. 테스트 시나리오 3: 상품 정보 조회

```text
당좌대월 수수료를 피하려면 어떻게 해야 하나요?
```

```text
개인 뱅킹 계좌의 수수료는 어떻게 되나요?
```

확인 포인트:

- Orchestrator Agent가 Product Information Agent로 라우팅하는지 확인
- Knowledge 문서를 기반으로 답변하는지 확인
- 수수료, 면제 조건, 유의사항이 명확히 설명되는지 확인

---

## 33. 테스트 시나리오 4: 당좌대월 승인

```text
내 계좌 IBAN DE89320895326389021994에 대해 4000유로 당좌대월을 요청하고 싶습니다.
```

또는 다음과 같이 입력할 수 있습니다.

```text
내 계좌 IBAN DE89320895326389021994에 대해 4000유로 당좌대월을 승인해 주세요.
```

확인 포인트:

- Orchestrator Agent가 해당 요청을 권한 업무로 인식하는지 확인
- Teller Agent 또는 Back Office Agent 흐름으로 연결되는지 확인
- approve-overdraft Tool이 호출되는지 확인
- 승인 결과가 명확히 표시되는지 확인

---

## 34. 테스트 시나리오 5: 고액 송금 후 환불 요청

먼저 4,000 EUR 송금을 요청합니다.

```text
IBAN DE89320895326389021994 계좌에서 IBAN DE89929842579913662103 계좌로 4000유로를 이체하고 싶습니다.
```

이후 환불 또는 취소 요청을 입력합니다.

```text
아, 실수했네요. 이전에 보낸 4000유로 송금을 취소해서 제 계좌 IBAN DE89320895326389021994로 되돌려줄 수 있나요?
```

확인 포인트:

- Teller Agent가 일반 송금을 처리하는지 확인
- 환불 또는 수수료 조정이 필요한 요청을 Back Office Agent로 위임하는지 확인
- fee-reversal Tool 또는 관련 권한 업무 처리가 수행되는지 확인
- 고객에게 처리 결과가 명확히 안내되는지 확인

---

# Part 6. 실습 점검표

## 35. 에이전트 구성 점검

| 점검 항목 | 완료 여부 |
|---|---|
| Back Office Agent를 생성했다 |  |
| Back Office Agent에 approve-overdraft Tool을 연결했다 |  |
| Back Office Agent에 fee-reversal Tool을 연결했다 |  |
| Back Office Agent의 Home page를 비활성화했다 |  |
| Teller Agent를 생성했다 |  |
| Teller Agent에 balance-inquiry Tool을 연결했다 |  |
| Teller Agent에 iban-transfer Tool을 연결했다 |  |
| Teller Agent에 Back Office Agent를 협업 에이전트로 추가했다 |  |
| Teller Agent의 Home page를 비활성화했다 |  |
| Product Information Agent를 생성했다 |  |
| Product Information Agent에 Knowledge 문서를 연결했다 |  |
| Product Information Agent의 Home page를 비활성화했다 |  |
| Bank Orchestrator Agent를 생성했다 |  |
| Bank Orchestrator Agent에 Teller Agent를 추가했다 |  |
| Bank Orchestrator Agent에 Product Information Agent를 추가했다 |  |
| Bank Orchestrator Agent의 Home page를 활성화했다 |  |
| 모든 에이전트를 Deploy했다 |  |

---

## 36. 테스트 점검

| 테스트 | 기대 결과 | 완료 여부 |
|---|---|---|
| 잔액 조회 | Teller Agent가 Tool을 호출해 잔액 조회 |  |
| 소액 송금 | Teller Agent가 송금 Tool 호출 |  |
| 상품 정보 질문 | Product Information Agent가 Knowledge 기반 답변 |  |
| 당좌대월 요청 | Back Office Agent 흐름으로 권한 업무 처리 |  |
| 환불 요청 | Back Office Agent 흐름으로 환불 또는 조정 처리 |  |

---

# Part 7. 자주 발생하는 문제

## 37. Tool이 보이지 않는 경우

다음을 확인합니다.

- `bank.yaml` 파일을 올바르게 업로드했는지 확인
- 필요한 Operation을 선택했는지 확인
- Tool 추가 후 **Done**을 클릭했는지 확인
- 에이전트를 저장했는지 확인

## 38. Orchestrator가 원하는 에이전트로 연결하지 않는 경우

다음을 확인합니다.

- Orchestrator Agent의 Instructions에 본인 에이전트 이름이 정확히 들어갔는지 확인
- Teller Agent와 Product Information Agent가 협업 에이전트로 추가되었는지 확인
- 각 전문 에이전트가 Deploy 상태인지 확인
- 요청 문장이 너무 모호하지 않은지 확인

## 39. Back Office Agent가 호출되지 않는 경우

다음을 확인합니다.

- Teller Agent에 Back Office Agent를 협업 에이전트로 추가했는지 확인
- Teller Agent Instructions에 당좌대월, 환불, 수수료 취소 요청 시 Back Office Agent로 라우팅하라는 지침이 있는지 확인
- Back Office Agent가 Deploy 상태인지 확인

## 40. Chat 화면에 여러 에이전트가 보이는 경우

다음을 확인합니다.

- Back Office Agent의 Home page가 비활성화되어 있는지 확인
- Teller Agent의 Home page가 비활성화되어 있는지 확인
- Product Information Agent의 Home page가 비활성화되어 있는지 확인
- Bank Orchestrator Agent의 Home page만 활성화되어 있는지 확인

---

# Part 8. 마무리

이번 실습에서는 watsonx Orchestrate를 활용해 은행 업무를 처리하는 Agentic AI 솔루션을 구성했습니다.

이번 시간의 핵심은 다음과 같습니다.

- 하나의 에이전트가 모든 업무를 처리하지 않아도 됩니다.
- 업무 성격에 따라 전문 에이전트를 나누면 유지보수와 확장이 쉬워집니다.
- Tool을 연결하면 실제 업무 시스템과 연동되는 에이전트를 만들 수 있습니다.
- Knowledge를 연결하면 문서 기반 답변을 제공할 수 있습니다.
- Orchestrator Agent를 사용하면 사용자는 하나의 창구만 이용해도 내부적으로 여러 에이전트가 협업할 수 있습니다.

즉, 이번 6교시는 앞에서 학습한 내용을 종합하여 **도구 기반 업무 처리 + 문서 기반 질의응답 + 에이전트 협업 + 오케스트레이션**을 모두 경험하는 실습입니다.

---

## 41. 참고 링크

- IBM watsonx Orchestrate 제품 페이지
- IBM Agentic AI 소개 자료
- IBM Banking and Financial Markets 산업 페이지
