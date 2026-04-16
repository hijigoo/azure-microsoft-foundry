import json
import uuid
import time

import httpx
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

API_BASE = "https://jsonplaceholder.typicode.com"


def _gen_id(prefix: str) -> str:
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    return f"{prefix}_{raw[:48]}"


def _extract_text(raw_input) -> str:
    if isinstance(raw_input, str):
        return raw_input
    if isinstance(raw_input, list):
        for item in raw_input:
            if isinstance(item, dict) and item.get("role") == "user":
                content = item.get("content", "")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") in ("input_text", "text")]
                    return " ".join(parts)
    return str(raw_input)


def _build_response(response_id: str, text: str) -> dict:
    return {
        "id": response_id,
        "object": "response",
        "created_at": int(time.time()),
        "status": "completed",
        "output": [
            {
                "type": "message",
                "id": _gen_id("msg"),
                "role": "assistant",
                "content": [{"type": "output_text", "text": text}],
            }
        ],
    }


def call_api(user_text: str) -> str:
    """사용자 입력에 따라 JSONPlaceholder API 호출"""
    endpoints = {
        "post": "/posts/1",
        "user": "/users/1",
        "comment": "/comments/1",
        "album": "/albums/1",
        "photo": "/photos/1",
        "todo": "/todos/1",
    }

    # 사용자 입력에서 키워드 매칭, 없으면 /posts/1
    path = "/posts/1"
    for keyword, ep in endpoints.items():
        if keyword in user_text.lower():
            path = ep
            break

    url = f"{API_BASE}{path}"
    try:
        resp = httpx.get(url, timeout=10)
        data = resp.json()
        return f"[API] GET {url}\n[Status] {resp.status_code}\n[Response]\n{json.dumps(data, indent=2, ensure_ascii=False)}"
    except Exception as e:
        return f"[API] GET {url}\n[Error] {e}"


async def handle_responses(request: Request):
    body = await request.json()
    raw_input = body.get("input", "")
    stream = body.get("stream", False)

    user_text = _extract_text(raw_input)
    text = call_api(user_text)

    response_id = _gen_id("resp")

    if stream:
        return StreamingResponse(
            _stream_response(response_id, text),
            media_type="text/event-stream",
        )

    return JSONResponse(_build_response(response_id, text))


async def _stream_response(response_id, text):
    yield f"event: response.created\ndata: {json.dumps({'type': 'response.created', 'response': {'id': response_id, 'object': 'response', 'status': 'in_progress'}})}\n\n"
    yield f"event: response.output_text.delta\ndata: {json.dumps({'type': 'response.output_text.delta', 'delta': text})}\n\n"
    yield f"event: response.output_text.done\ndata: {json.dumps({'type': 'response.output_text.done', 'text': text})}\n\n"
    yield f"event: response.completed\ndata: {json.dumps({'type': 'response.completed', 'response': _build_response(response_id, text)})}\n\n"


async def health(request: Request):
    return JSONResponse({"status": "ok"})


app = Starlette(
    routes=[
        Route("/responses", handle_responses, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
        Route("/readiness", health, methods=["GET"]),
        Route("/liveness", health, methods=["GET"]),
    ]
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8088)
