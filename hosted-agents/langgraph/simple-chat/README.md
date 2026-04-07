# Simple Chat Agent

LangGraph 기반의 가장 심플한 Hosted Agent입니다. Tool 없이 LLM만 호출하여 응답합니다.

## 파일 구조

| 파일 | 설명 |
|------|------|
| `main.py` | LangGraph 에이전트 코드 (`START → llm_call → END`) |
| `agent.yaml` | Foundry 에이전트 메타데이터 |
| `Dockerfile` | 컨테이너 빌드 (`python:3.12-slim`, 포트 `8088`) |
| `requirements.txt` | 의존성 (버전 고정) |
| `deploy.ipynb` | 배포 노트북 (로컬 테스트 + Python SDK 배포) |
| `.env.example` | 환경변수 템플릿 |

## 빠른 시작

```bash
cp .env.example .env
# .env 값 채우기

source .venv/bin/activate
pip install -r requirements.txt
export $(grep -v '^#' .env | xargs)
python main.py
```

테스트:
```bash
curl -X POST http://localhost:8088/responses \
  -H "Content-Type: application/json" \
  -d '{"input": "hello", "stream": false}'
```

## 배포

`deploy.ipynb` 노트북을 참고하세요.

## 환경변수

| 변수 | 설명 |
|------|------|
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry 프로젝트 엔드포인트 |
| `AZURE_AI_MODEL_DEPLOYMENT_NAME` | 모델 배포 이름 (예: `gpt-4.1`) |

## 참고

- [Deploy a hosted agent](https://learn.microsoft.com/azure/foundry/agents/how-to/deploy-hosted-agent)
- [Manage hosted agent lifecycle](https://learn.microsoft.com/azure/foundry/agents/how-to/manage-hosted-agent)
