# Echo Chat Agent

LLM 호출 없이 입력을 그대로 Echo하는 더미 에이전트입니다.

## 목적

- Hosted Agent **인터페이스(Responses API)가 정상 동작하는지** 최소 비용으로 검증
- LLM, Azure 인증 등 외부 의존성 없이 컨테이너 ↔ Foundry 간 통신만 확인

## 동작

```
사용자: "안녕"
에이전트: "Echo: 안녕"
```

## 의존성

`starlette`, `uvicorn` — 2개만 사용 (Azure SDK 없음)

## 배포

`deploy.ipynb` 참고
