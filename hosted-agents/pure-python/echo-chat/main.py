import json
import uuid
import time

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route


def _gen_id(prefix: str) -> str:
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    return f"{prefix}_{raw[:48]}"


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


async def handle_responses(request: Request):
    body = await request.json()
    raw_input = body.get("input", "")
    stream = body.get("stream", False)

    # 사용자 텍스트 추출
    user_text = raw_input
    if isinstance(raw_input, list):
        for item in raw_input:
            if isinstance(item, dict) and item.get("role") == "user":
                content = item.get("content", "")
                if isinstance(content, str):
                    user_text = content
                elif isinstance(content, list):
                    parts = [p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") in ("input_text", "text")]
                    user_text = " ".join(parts)
                break
    elif isinstance(raw_input, str):
        user_text = raw_input

    text = f"Echo: {user_text}"

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
