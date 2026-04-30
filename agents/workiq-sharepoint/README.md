# WorkIQ SharePoint Agent

Microsoft Foundry Agents SDK의 `SharepointTool`을 이용해 사내 WorkIQ SharePoint 문서를 검색·요약하는 에이전트 샘플입니다.

## 구성

- `agent.ipynb` — 에이전트 생성 → thread → run 까지 SDK 사용 예제
- `.env.example` — 필요한 환경변수 템플릿

## 사용 방법

```bash
cp .env.example .env
# .env 파일을 채운 뒤
az login
```

이후 `agent.ipynb`를 위에서부터 실행합니다.

## 사전 준비

1. **WorkIQ SharePoint connection** 등록 — Foundry portal의 *Build > Tools*에서 WorkIQ SharePoint 연결을 만들고 이름을 `.env`의 `WORKIQ_SHAREPOINT_CONNECTION_NAME`에 기입
2. **모델 배포** — Foundry 프로젝트에 `gpt-4.1` 등 채팅 모델 배포
3. **권한** — 실행 계정에 `Azure AI User` 역할

## 참고

- [SharePoint tool samples](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/sharepoint-samples)
- `SharepointTool`은 `azure-ai-agents>=1.2.0b1` (beta)에서만 제공됩니다.
