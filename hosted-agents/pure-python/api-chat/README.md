# API Chat Agent

외부 API(JSONPlaceholder)를 호출하여 Hosted Agent에서 **외부 네트워크 통신이 가능한지** 확인하는 에이전트입니다.

## 목적

- Hosted Agent 컨테이너에서 **외부 인터넷(아웃바운드)** 접근이 가능한지 검증
- LLM 없이 순수 HTTP 요청으로 외부 API 호출 테스트

## 동작

사용자 입력에 포함된 키워드에 따라 `https://jsonplaceholder.typicode.com` API를 호출합니다.

| 키워드 | API 엔드포인트 |
|---|---|
| `post` | `/posts/1` |
| `user` | `/users/1` |
| `todo` | `/todos/1` |
| `comment` | `/comments/1` |
| 기타 | `/posts/1` (기본) |

```
사용자: "todo 확인"
에이전트: [API] GET https://jsonplaceholder.typicode.com/todos/1
         [Status] 200
         [Response] {"userId": 1, "id": 1, "title": "delectus aut autem", "completed": false}
```

## 의존성

`starlette`, `uvicorn`, `httpx` — 3개만 사용 (Azure SDK 없음)

## 배포

`deploy.ipynb` 참고
