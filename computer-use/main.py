import os
import base64
import logging
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, ComputerUsePreviewTool

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ENDPOINT = os.getenv("AZURE_AI_PROJECT_ENDPOINT")
SCREENSHOT_DIR = os.getenv("SCREENSHOT_DIR", "./screenshots")


def encode_screenshot(filepath: str) -> str:
    """스크린샷 파일을 base64 data URL로 인코딩"""
    with open(filepath, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/png;base64,{data}"


def main():
    # 1. AIProjectClient 생성
    project = AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )

    # 2. Computer Use Tool로 에이전트 생성
    computer_use_tool = ComputerUsePreviewTool(
        display_width=1920,
        display_height=1080,
        environment="windows",
    )

    agent = project.agents.create_version(
        agent_name="computer-use-agent",
        description="Computer use agent that interacts with UI through screenshots",
        definition=PromptAgentDefinition(
            model="computer-use-preview",
            instructions="""
            You are a computer automation assistant.
            Be direct and efficient. When you reach the search results page,
            read and describe the actual search result titles and descriptions you can see.
            """,
            tools=[computer_use_tool],
        ),
    )
    logger.info(f"Agent created: {agent.name}, version: {agent.version}")

    # 3. OpenAI 클라이언트로 초기 요청
    openai = project.get_openai_client()

    # 초기 스크린샷 (screenshots/initial.png 필요)
    initial_screenshot = os.path.join(SCREENSHOT_DIR, "initial.png")
    if not os.path.exists(initial_screenshot):
        logger.error(f"초기 스크린샷이 필요합니다: {initial_screenshot}")
        logger.info("스크린샷을 캡처하여 screenshots/initial.png 로 저장하세요.")
        project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        return

    screenshot_url = encode_screenshot(initial_screenshot)

    response = openai.responses.create(
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "I need you to help me search for 'Microsoft Foundry'. "
                        "Please type 'Microsoft Foundry' and submit the search. "
                        "Once you see search results, the task is complete.",
                    },
                    {
                        "type": "input_image",
                        "image_url": screenshot_url,
                    },
                ],
            }
        ],
        extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        truncation="auto",
    )
    logger.info(f"Initial response received (ID: {response.id})")

    # 4. 반복 루프 - 모델이 요청하는 액션을 처리
    max_iterations = 10
    iteration = 0

    while True:
        if iteration >= max_iterations:
            logger.warning(f"최대 반복 횟수({max_iterations})에 도달. 중지합니다.")
            break

        iteration += 1
        logger.info(f"--- Iteration {iteration} ---")

        # computer_call 확인
        computer_calls = [item for item in response.output if item.type == "computer_call"]

        if not computer_calls:
            # 최종 출력
            for item in response.output:
                if hasattr(item, "content"):
                    for content in item.content:
                        if hasattr(content, "text"):
                            print(f"\n최종 결과: {content.text}")
            break

        # 첫 번째 computer_call 처리
        computer_call = computer_calls[0]
        action = computer_call.action
        call_id = computer_call.call_id

        logger.info(f"Action: {action.type}")
        if action.type == "click":
            logger.info(f"  Click at ({action.x}, {action.y})")
        elif action.type == "type":
            logger.info(f"  Type: {action.text}")
        elif action.type == "scroll":
            logger.info(f"  Scroll at ({action.x}, {action.y})")
        elif action.type == "screenshot":
            logger.info("  Screenshot requested")

        # ⚠️ 여기에 실제 액션 실행 코드를 구현하세요
        # 예: pyautogui, Playwright 등으로 클릭/타이핑/스크롤 수행
        # 그 후 새 스크린샷을 캡처

        # 시뮬레이션: 같은 스크린샷을 다시 전송 (실제로는 새 스크린샷 필요)
        next_screenshot = encode_screenshot(initial_screenshot)

        # safety check 처리
        acknowledged_safety_checks = []
        if hasattr(computer_call, "pending_safety_checks") and computer_call.pending_safety_checks:
            for check in computer_call.pending_safety_checks:
                logger.warning(f"Safety check: {check.code} - {check.message}")
                acknowledged_safety_checks.append(
                    {"id": check.id, "code": check.code, "message": check.message}
                )

        # 다음 요청
        input_data = {
            "call_id": call_id,
            "type": "computer_call_output",
            "output": {
                "type": "computer_screenshot",
                "image_url": next_screenshot,
            },
        }
        if acknowledged_safety_checks:
            input_data["acknowledged_safety_checks"] = acknowledged_safety_checks

        response = openai.responses.create(
            previous_response_id=response.id,
            input=[input_data],
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
            truncation="auto",
        )
        logger.info(f"Response received (ID: {response.id})")

    # 5. 정리
    project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    logger.info("Agent deleted")


if __name__ == "__main__":
    main()
