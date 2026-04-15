# Simple Chat Agent (Pure Python)

프레임워크 없이 순수 Python으로 구현한 Hosted Agent입니다. LangGraph/LangChain 없이 OpenAI SDK + Starlette만으로 Foundry Responses API 인터페이스를 직접 구현합니다.

## langgraph 버전과의 차이

| | langgraph 버전 | pure-python 버전 |
|---|---|---|
| 프레임워크 | LangGraph + LangChain | 없음 |
| 어댑터 | `azure-ai-agentserver-langgraph` | 직접 구현 |
| LLM 호출 | `langchain.chat_models.init_chat_model` | `openai.AzureOpenAI` |
| HTTP 서버 | 어댑터가 자동 생성 | Starlette 직접 구성 |
| 의존성 수 | 6개 패키지 | 4개 패키지 |

## 아키텍처

```
사용자 → Foundry Agent Service → 컨테이너 (main.py) → Azure OpenAI
```

- `main.py`에서 Starlette 앱으로 `/responses` 엔드포인트 직접 구현
- OpenAI SDK(`AzureOpenAI`)로 Azure OpenAI 호출
- 스트리밍/비스트리밍 모두 지원
- 컨테이너는 포트 `8088`에서 실행되며, Foundry가 이 컨테이너를 Azure Container Apps에 배포

## 파일 구조

| 파일 | 설명 |
|------|------|
| `main.py` | 순수 Python 에이전트 코드 (Starlette + OpenAI SDK) |
| `agent.yaml` | Foundry 에이전트 메타데이터 (azd 배포용) |
| `Dockerfile` | 컨테이너 빌드 (`python:3.12-slim`, 포트 `8088`) |
| `requirements.txt` | 의존성 (버전 고정, 4개만) |
| `deploy.ipynb` | 배포 노트북 (로컬 테스트 + Python SDK 배포) |

## 사전 준비 (최초 1회)

1. **Capability Host 생성** — Foundry 계정에 에이전트 컨테이너 호스팅 환경 활성화
2. **RBAC 권한 부여** — Foundry 프로젝트의 Managed Identity에:
   - `AcrPull` — Container Registry에서 이미지 Pull
   - `Azure AI User` — Foundry 리소스에서 API 접근
3. **모델 배포** — Foundry 프로젝트에 사용할 모델(예: `gpt-4.1`) 배포
4. **`.env` 작성** — `.env.example`을 복사하여 값 채우기

> 자세한 내용은 `deploy.ipynb` 노트북 참고

## 배포 전 로컬 테스트

Agent 실행:
```bash
cp .env.example .env
# .env 값 채우기

source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
python main.py
```

테스트 (비스트리밍):
```bash
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "hello", "stream": false}'
```

테스트 (스트리밍):
```bash
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "hello", "stream": true}'
```

## Hosted Agent 배포

`deploy.ipynb` 노트북을 참고하세요. 주요 단계:

1. Docker 이미지 빌드 & ACR 푸시 (`--platform=linux/amd64` 필수)
2. Container Registry 권한 설정 (AcrPull)
3. Capability Host 생성
4. Python SDK로 Hosted Agent 생성 (`project.agents.create_version`)
5. Agent 테스트 (`openai_client.responses.create` + `agent_reference`)

## 환경변수

| 변수 | 설명 |
|------|------|
| `SUBSCRIPTION_ID` | Azure 구독 ID — Capability Host 생성 시 사용 |
| `RESOURCE_GROUP` | 리소스 그룹 이름 — Capability Host 생성 시 사용 |
| `ACCOUNT_NAME` | Foundry 계정(리소스) 이름 — Capability Host 생성 시 사용 |
| `ACR_NAME` | Azure Container Registry 이름 — Docker 이미지 빌드 & 푸시 시 사용 |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 — 에이전트가 모델 호출 시 사용 |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry 프로젝트 엔드포인트 — SDK 클라이언트에서 사용 |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | 모델 배포 이름 (예: `gpt-4.1`) — 에이전트가 호출할 모델 지정 |

## 주의사항

- **Apple Silicon(M1/M2/M3/M4)** 맥북에서는 Docker 빌드 시 `--platform=linux/amd64` 필수
- **`OPENAI_API_VERSION`** — 코드에서는 사용하지 않지만, Foundry 컨테이너 배포 시 환경변수로 `2025-03-01-preview`를 명시해야 함

## 참고

- [Deploy a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Manage hosted agent lifecycle](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent)
