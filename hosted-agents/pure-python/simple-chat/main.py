import os
import json
import uuid
import time
import logging

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, StreamingResponse
from starlette.routing import Route

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a helpful assistant."

_client = None


def get_openai_client() -> AzureOpenAI:
    global _client
    if _client is None:
        credential = DefaultAzureCredential()
        token_provider = get_bearer_token_provider(
            credential, "https://cognitiveservices.azure.com/.default"
        )
        _client = AzureOpenAI(
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            azure_ad_token_provider=token_provider,
            api_version=os.getenv("OPENAI_API_VERSION", "2025-03-01-preview"),
        )
    return _client


def _convert_content(content):
    """Responses API content 형식을 Chat Completions API 형식으로 변환"""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        converted = []
        for part in content:
            if isinstance(part, dict):
                t = part.get("type", "")
                if t == "input_text":
                    converted.append({"type": "text", "text": part.get("text", "")})
                elif t == "input_image":
                    converted.append({"type": "image_url", "image_url": part.get("image_url", "")})
                else:
                    converted.append(part)
            else:
                converted.append(part)
        return converted
    return content


def _parse_input(raw_input):
    """input 필드를 OpenAI messages 형식으로 변환"""
    if isinstance(raw_input, str):
        return [{"role": "user", "content": raw_input}]
    if isinstance(raw_input, list):
        messages = []
        for item in raw_input:
            if isinstance(item, dict) and "role" in item:
                messages.append({
                    "role": item["role"],
                    "content": _convert_content(item.get("content", "")),
                })
            elif isinstance(item, str):
                messages.append({"role": "user", "content": item})
        return messages
    return [{"role": "user", "content": str(raw_input)}]


def _gen_id(prefix: str) -> str:
    """Foundry 호환 ID 생성 (body 길이 48자)"""
    raw = uuid.uuid4().hex + uuid.uuid4().hex
    return f"{prefix}_{raw[:48]}"


def _build_response(response_id: str, text: str) -> dict:
    """Responses API 형식으로 응답 구성"""
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

    print(f"\n>>> [INPUT] raw_input: {json.dumps(raw_input, ensure_ascii=False, default=str)}")
    print(f">>> [STREAM] {stream}")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + _parse_input(raw_input)
    model = os.getenv("AZURE_AI_MODEL_DEPLOYMENT_NAME", "gpt-4.1")
    response_id = _gen_id("resp")
    client = get_openai_client()

    if stream:
        return StreamingResponse(
            _stream_response(client, model, messages, response_id),
            media_type="text/event-stream",
        )

    completion = client.chat.completions.create(model=model, messages=messages)
    text = completion.choices[0].message.content or ""
    print(f"<<< [OUTPUT] {text}")
    return JSONResponse(_build_response(response_id, text))


async def _stream_response(client, model, messages, response_id):
    """SSE 스트리밍 응답 생성"""
    # response.created
    yield f"event: response.created\ndata: {json.dumps({'type': 'response.created', 'response': {'id': response_id, 'object': 'response', 'status': 'in_progress'}})}\n\n"

    collected = []
    stream = client.chat.completions.create(model=model, messages=messages, stream=True)

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            delta = chunk.choices[0].delta.content
            collected.append(delta)
            event_data = {
                "type": "response.output_text.delta",
                "delta": delta,
            }
            yield f"event: response.output_text.delta\ndata: {json.dumps(event_data)}\n\n"

    full_text = "".join(collected)
    print(f"<<< [OUTPUT] {full_text}")

    # response.output_text.done
    yield f"event: response.output_text.done\ndata: {json.dumps({'type': 'response.output_text.done', 'text': full_text})}\n\n"

    # response.completed
    yield f"event: response.completed\ndata: {json.dumps({'type': 'response.completed', 'response': _build_response(response_id, full_text)})}\n\n"


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
