# Azure Microsoft Foundry - Hosted Agent 샘플

Microsoft Foundry에 Hosted Agent를 배포하는 다양한 샘플 프로젝트 모음입니다.

## Hosted Agents

### LangGraph 기반

| 에이전트 | 설명 | 검증 포인트 |
|---|---|---|
| [langgraph/simple-chat](hosted-agents/langgraph/simple-chat/) | LangGraph + LangChain + `azure-ai-agentserver-langgraph` 어댑터 | LangGraph 프레임워크 기반 Hosted Agent 배포 |

### Pure Python (프레임워크 없음)

| 에이전트 | 설명 | 검증 포인트 |
|---|---|---|
| [pure-python/echo-chat](hosted-agents/pure-python/echo-chat/) | 입력을 그대로 Echo하는 더미 에이전트 (LLM 없음) | Responses API **응답 형식만 맞추면** Hosted Agent로 동작 가능한지 |
| [pure-python/api-chat](hosted-agents/pure-python/api-chat/) | 외부 API(JSONPlaceholder) 호출 에이전트 (LLM 없음) | 컨테이너에서 **외부 네트워크(아웃바운드)** 통신이 가능한지 |
| [pure-python/simple-chat](hosted-agents/pure-python/simple-chat/) | OpenAI SDK + Starlette로 Responses API 직접 구현 | 프레임워크 없이 순수 Python으로 **LLM 호출**이 가능한지 |

## 사전 준비

1. **Capability Host 생성** — Foundry 계정에 에이전트 컨테이너 호스팅 환경 활성화
2. **RBAC 권한 부여** — `AcrPull` + `Azure AI User`
3. **모델 배포** — LLM 사용 에이전트의 경우 (echo-chat, api-chat은 불필요)

## Hosted Agent 구현 시 주의사항

- **필수 엔드포인트**: `/responses` (POST), `/readiness` (GET), `/liveness` (GET)
- **응답 ID body 길이**: prefix 뒤의 body 부분이 48자 필수 (예: `resp_` + 48자 hex = 53자)
- **입력 타입 변환**: Foundry는 `input_text` 타입으로 전달하므로 Chat Completions API 사용 시 `text` 타입으로 변환 필요

각 에이전트 폴더의 `deploy.ipynb`에서 배포할 수 있습니다.
