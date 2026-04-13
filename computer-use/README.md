# Computer Use Agent

Microsoft Foundry의 `computer-use-preview` 모델을 사용하여 스크린샷 기반으로 UI를 자동화하는 에이전트입니다.

## 아키텍처

```
사용자 → main.py → Foundry Agent (computer-use-preview)
                        ↓
              스크린샷 분석 → 액션 제안 (click/type/scroll)
                        ↓
              앱에서 액션 실행 → 새 스크린샷 캡처 → 반복
```

> ⚠️ 모델이 직접 컴퓨터를 제어하지 않습니다. 모델은 액션을 **제안**하고, 앱이 **실행**합니다.

## 사전 준비

- **`computer-use-preview` 모델 접근 신청** — [신청 폼](https://aka.ms/oai/cuaaccess)
- **모델 배포** — `computer-use-preview` 모델을 Foundry 프로젝트에 배포 (지원 리전: `eastus2`, `swedencentral`, `southindia`)
- **가상 머신 또는 샌드박스 환경** — 민감한 데이터가 없는 환경에서 실행 권장
- **`.env` 작성** — `.env.example`을 복사하여 값 채우기

## 파일 구조

| 파일 | 설명 |
|------|------|
| `main.py` | Computer Use 에이전트 메인 코드 |
| `requirements.txt` | 의존성 |
| `.env.example` | 환경변수 템플릿 |
| `screenshots/` | 스크린샷 저장 디렉토리 (`initial.png` 필요) |

## 실행

```bash
cp .env.example .env
# .env 값 채우기

source .venv/bin/activate
pip install -r requirements.txt

# screenshots/initial.png 에 초기 스크린샷 저장
python main.py
```

## 동작 흐름

1. `computer-use-preview` 모델로 에이전트 생성
2. 초기 스크린샷 + 작업 지시를 전송
3. 모델이 `computer_call`로 액션 제안 (click, type, scroll, screenshot)
4. 앱에서 액션 실행 → 새 스크린샷 캡처 → 모델에 전송
5. 작업 완료될 때까지 반복 (최대 10회)
6. 에이전트 삭제

## 환경변수

| 변수 | 설명 |
|------|------|
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry 프로젝트 엔드포인트 |
| `SCREENSHOT_DIR` | 스크린샷 저장 경로 (기본: `./screenshots`) |

## 주의사항

- **보안** — 민감한 데이터가 있는 머신에서 실행하지 마세요
- **Safety Check** — 모델이 `pending_safety_checks`를 반환하면 사용자가 확인 후 진행해야 합니다
- **실제 액션 실행** — `main.py`의 액션 실행 부분에 `pyautogui`, `Playwright` 등을 연동해야 합니다

## 참고

- [Computer Use Tool 공식 문서](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/computer-use)
- [Python SDK 샘플](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/agents/tools)
- [접근 신청](https://aka.ms/oai/cuaaccess)
