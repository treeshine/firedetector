# AI 감지 클라이언트 가이드 (AI Detection Client Guide)

## 📌 개요
`model_develop/main.py`는 이 프로젝트의 핵심인 **실시간 화재 및 동물 감지**를 담당하는 스크립트입니다.  
OpenCV를 통해 카메라 영상을 획득하고, YOLOv8 모델을 사용하여 객체를 감지하며, 화재 발생 시 Google Gemini API를 통해 정밀 분석을 수행합니다.

## ⚙️ 주요 기능
1.  **실시간 영상 캡처**: OpenCV를 사용하여 웹캠 또는 비디오 소스에서 프레임을 읽어옵니다.
2.  **이중 YOLO 모델 운용**:
    *   `fireModel/best.pt`: 화재(Fire, Smoke) 감지 전용 모델
    *   `fireModel/yolov8s.pt`: 동물(Dog, Cat, Bird 등) 감지용 일반 모델
3.  **Gemini Vision 분석**: 화재가 감지되고 일정 시간이 지나면, 해당 프레임을 Google Gemini API로 전송하여 상황을 텍스트로 분석합니다.
4.  **네트워크 통신**:
    *   **TCP 소켓**: 로컬 클라이언트(예: Streamlit UI)에 영상 프레임과 이벤트 데이터를 전송합니다.
    *   **WebSocket**: 백엔드 서버로 실시간 영상 스트림을 전송합니다.
    *   **HTTP**: 화재 감지 시 백엔드 API(`api/v1/notify`)를 호출하여 알림을 보냅니다.

## 🛠️ 설정 및 환경 변수
스크립트 실행 전, 필요한 환경 변수와 설정값을 확인하십시오.

### 모델 설정
```python
fire_model = YOLO("fireModel/best.pt")      # 화재 감지 모델 경로
animal_model = YOLO("fireModel/yolov8s.pt") # 동물 감지 모델 경로
TARGET_CLASS = ['fire', 'smoke']            # 화재 감지 대상 클래스
ANIMAL_CLASSES = ['dog', 'cat', 'bird']     # 동물 감지 대상 클래스
```

### 통신 설정
```python
# .env 파일 또는 시스템 환경 변수에서 로드
WEBSOCKET_URI = f"ws://{os.getenv('FASTAPI_SERVER')}/ws/v1/"
NOTIFY_API_URL = f"http://{os.getenv('FASTAPI_SERVER')}/api/v1/notify"
HOST = os.getenv("BIND_ADDRESS") # TCP 서버 바인딩 주소
PORT = int(os.getenv("BIND_PORT")) # TCP 서버 포트
```

> [!WARNING]
> **환경 변수 확인 필수**  
> `FASTAPI_SERVER`, `BIND_ADDRESS`, `BIND_PORT` 환경 변수가 설정되어 있지 않으면 통신 오류가 발생할 수 있습니다. `.env` 파일을 확인하거나 시스템 환경 변수를 설정해주세요.

## 🔄 동작 로직 상세

### 1. 화재 감지 및 검증 프로세스
오탐(False Positive)을 줄이기 위해 다음과 같은 검증 단계를 거칩니다.

1.  **최초 감지**: YOLO 모델이 화재를 감지하면 `pending_fire_check_time`을 기록하고 대기합니다.
2.  **지속성 확인**: `FIRE_CHECK_DELAY`(기본 10초) 동안 화재가 지속적으로 감지되어야 "확정"으로 간주합니다.
3.  **Gemini 분석**: 화재가 확정되면 `run_gemini_analysis_thread`를 통해 Gemini API에 이미지를 전송하고 분석 결과를 받습니다.
4.  **모니터링**: 화재가 확정된 이후에는 `GEMINI_CHECK_INTERVAL`(기본 30초)마다 주기적으로 Gemini 분석을 수행합니다.
5.  **종료**: `FIRE_RESET_INTERVAL`(기본 60초) 동안 화재가 감지되지 않으면 모니터링 상태를 해제합니다.

### 2. 데이터 전송 프로토콜 (TCP)
로컬 UI와의 통신을 위해 자체적인 바이너리 프로토콜을 사용합니다.
패킷 구조: `[Payload Size (4 bytes)] + [Message Type (1 byte)] + [Payload]`

| 메시지 타입 (Hex) | 설명 | Payload 형식 |
| :--- | :--- | :--- |
| `0x01` | 영상 프레임 | JPEG 이미지 바이트 |
| `0x02` | 화재 이벤트 | JSON 문자열 |
| `0x03` | 동물 이벤트 | JSON 문자열 |
| `0x04` | Gemini 분석 결과 | JSON 문자열 |

## � 설치 및 환경 구성

프로젝트를 처음 클론(Clone)한 경우, 아래 절차를 따라 가상 환경을 설정하고 의존성 패키지를 설치해야 합니다.

### 1. 가상 환경 생성
`model_develop` 디렉토리 내에 `fire_env`라는 이름의 가상 환경을 생성합니다.

```bash
cd model_develop
python -m venv fire_env
```

### 2. 가상 환경 활성화
운영체제에 맞는 명령어로 가상 환경을 활성화합니다.

*   **Windows (PowerShell)**:
    ```powershell
    .\fire_env\Scripts\Activate.ps1
    ```
*   **macOS / Linux**:
    ```bash
    source fire_env/bin/activate
    ```

### 3. 의존성 패키지 설치
가상 환경이 활성화된 상태에서 `requirements.txt`에 명시된 패키지들을 설치합니다.

```bash
pip install -r requirements.txt
```

## �🚀 실행 방법

가상 환경이 활성화된 상태에서 아래 명령어로 실행합니다.

```bash
cd model_develop
python main.py
```

실행 시 콘솔에 다음과 같은 로그가 출력되어야 정상입니다.
```text
화재 감지 모델 클래스: ['fire', 'smoke']
동물 감지 모델 클래스: ['dog', 'cat', 'bird', 'person']
--- 실시간 화재 + 동물 감지를 시작합니다 ---
✓ 소켓 서버 대기 중: 0.0.0.0:8555
```
