import cv2
from ultralytics import YOLO
import time
import math
import socket
import json
from datetime import datetime
import threading
from PIL import Image
from gemini_analyzer import analyze_frame_with_gemini
import asyncio
import websockets

# --- 설정 ---
fire_model = YOLO("fireModel/best.pt")  # 화재 감지 모델 (매 프레임)
animal_model = YOLO("fireModel/yolov8s.pt")  # 동물 감지 모델
WEBSOCKET_URI = "ws://localhost:8000/ws/v1"  # 실제 서버 주소로 변경
cap = cv2.VideoCapture(0)

ALERT_COOLDOWN = 30
last_alert_time = 0

# Gemini 분석 설정
GEMINI_CHECK_INTERVAL = 30  # 30초마다 확인
last_gemini_check_time = 0
FIRE_CHECK_DELAY = 10  # 화재 감지 후 10초 뒤에 재확인
pending_fire_check_time = None  # 재확인 대기 시작 시간

# 모니터링 상태 변수
is_monitoring_fire = False
last_fire_detection_time = 0
FIRE_RESET_INTERVAL = 60  # 화재가 60초 이상 감지되지 않으면 모니터링 종료
FIRE_LOG_INTERVAL = 3  # 화재 감지 로그 출력 간격 (초)
last_fire_log_time = 0

TARGET_CLASS = ['fire','smoke']  # 감지할 화재 클래스

# 동물 클래스 리스트 (YOLO coco 데이터셋의 동물 클래스)
ANIMAL_CLASSES = ['dog', 'cat', 'bird','person']

# 이벤트 로그 파일
FIRE_EVENT_LOG_FILE = "fire_events.json"
ANIMAL_EVENT_LOG_FILE = "animal_events.json"
GEMINI_LOG_FILE = "gemini_analysis_log.txt"

# 성능 최적화: 프레임 스킵 설정
ANIMAL_DETECTION_SKIP = 3  # 매 3프레임마다 동물 감지 (더 빠름)
frame_count = 0

print(f"화재 감지 모델 클래스: {TARGET_CLASS}")
print(f"동물 감지 모델 클래스: {ANIMAL_CLASSES}")
print(f"성능 최적화: 매 {ANIMAL_DETECTION_SKIP}프레임마다 동물 감지")
print(f"Gemini 분석: 매 {GEMINI_CHECK_INTERVAL}초마다 실행")
print("--- 실시간 화재 + 동물 감지를 시작합니다 ---")

# === WebSocket 관련 함수 ===
async def websocket_sender(frame_queue: asyncio.Queue):
    """WebSocket으로 프레임을 전송하는 비동기 함수"""
    global websocket_connection, websocket_connected
    
    while True:
        try:
            async with websockets.connect(WEBSOCKET_URI) as ws:
                websocket_connection = ws
                websocket_connected = True
                print(f"✓ WebSocket 연결됨: {WEBSOCKET_URI}")
                
                while True:
                    # 큐에서 프레임 데이터 가져오기
                    frame_data = await frame_queue.get()
                    if frame_data is None:  # 종료 신호
                        break
                    
                    try:
                        await ws.send(frame_data)
                    except websockets.exceptions.ConnectionClosed:
                        print("WebSocket 연결이 닫혔습니다. 재연결 시도...")
                        websocket_connected = False
                        break
                        
        except (websockets.exceptions.ConnectionClosedError, 
                websockets.exceptions.InvalidStatusCode,
                ConnectionRefusedError,
                OSError) as e:
            websocket_connected = False
            print(f"WebSocket 연결 실패: {e}. 3초 후 재연결...")
            await asyncio.sleep(3)
        except Exception as e:
            websocket_connected = False
            print(f"WebSocket 오류: {e}")
            await asyncio.sleep(3)


def run_websocket_thread(frame_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
    """별도 스레드에서 WebSocket 이벤트 루프 실행"""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(websocket_sender(frame_queue))


# WebSocket용 asyncio 이벤트 루프와 큐 생성
websocket_loop = asyncio.new_event_loop()
frame_queue = asyncio.Queue()

# WebSocket 스레드 시작
websocket_thread = threading.Thread(
    target=run_websocket_thread,
    args=(frame_queue, websocket_loop),
    daemon=True
)
websocket_thread.start()


def send_frame_via_websocket(frame):
    """프레임을 WebSocket 큐에 추가"""
    try:
        # JPEG로 압축
        ret_encode, frame_encoded = cv2.imencode(
            '.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if ret_encode:
            data = frame_encoded.tobytes()
            # 스레드 안전하게 큐에 추가
            websocket_loop.call_soon_threadsafe(frame_queue.put_nowait, data)
            return True
    except Exception as e:
        print(f"프레임 인코딩 오류: {e}")
    return False

# Gemini 분석을 수행하는 스레드 함수
def run_gemini_analysis_thread(frame_bgr):
    print(">>> Gemini 분석 스레드 진입")
    try:
        # OpenCV BGR -> PIL RGB 변환
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(frame_rgb)
        
        print(">>> Gemini API 호출 중...")
        # Gemini 분석 호출
        result = analyze_frame_with_gemini(pil_image)
        
        # 결과 출력 및 로깅
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] Gemini 분석 결과: {result}"
        print(f"\n>>> {log_message}\n")
        
        # 파일에 기록
        with open(GEMINI_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_message + "\n")
            
    except Exception as e:
        print(f"Gemini 스레드 오류: {e}")

# 로컬호스트에서 프레임을 송신할 소켓 서버 설정
HOST = 'localhost'
PORT = 5005

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(1)
server_socket.settimeout(1)

client_socket = None
print(f"✓ 소켓 서버 대기 중: {HOST}:{PORT}")

try:
    while True:
        # 클라이언트 연결 시도
        try:
            if client_socket is None:
                client_socket, addr = server_socket.accept()
                print(f"✓ 클라이언트 연결됨: {addr}")
        except socket.timeout:
            pass

        # 1. 카메라에서 프레임 읽기
        ret, frame = cap.read()
        if not ret:
            print("카메라를 읽을 수 없습니다.")
            break

        # 2. YOLO 모델로 현재 프레임 추론 (화재 감지 - 매 프레임)
        fire_results = fire_model(frame, stream=True, verbose=False)
        
        # 동물 감지는 성능 최적화를 위해 프레임 스킵
        animal_results = None
        if frame_count % ANIMAL_DETECTION_SKIP == 0:
            animal_results = animal_model(frame, stream=True, verbose=False)
        
        frame_count += 1

        fire_detected_in_frame = False
        animal_detected_in_frame = False
        detected_animals = []
        max_fire_confidence = 0.0

        # 3-1. 화재 감지 결과 분석 (매 프레임)
        for r in fire_results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                class_name = fire_model.names[cls_id]

                if class_name.lower() in [t.lower() for t in TARGET_CLASS]:
                    # 화재 이벤트 트리거
                    fire_detected_in_frame = True
                    
                    x1, y1, x2, y2 = box.xyxy[0]
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    
                    # 화재 감지: 파란색 박스
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)

                    conf = math.ceil(box.conf[0] * 100) / 100
                    if conf > max_fire_confidence:
                        max_fire_confidence = conf
                        
                    label = f"{class_name.upper()} {conf}"
                    cv2.putText(frame, label, (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # === 화재 감지 확인 및 Gemini 호출 로직 (수정됨) ===
        current_time = time.time()

        # 화재 감지 시간 업데이트
        if fire_detected_in_frame:
            last_fire_detection_time = current_time

        # 화재가 일정 시간 이상 감지되지 않으면 모니터링 종료
        if is_monitoring_fire and (current_time - last_fire_detection_time > FIRE_RESET_INTERVAL):
            print("--- 화재 소실 확인. 모니터링 종료 ---")
            is_monitoring_fire = False
            pending_fire_check_time = None

        if fire_detected_in_frame:
            if not is_monitoring_fire:
                # Case 1: 새로운 화재 감지 (모니터링 시작 전)
                if pending_fire_check_time is None:
                    # 10초 타이머 시작
                    pending_fire_check_time = current_time
                    print(f"화재 최초 감지. {FIRE_CHECK_DELAY}초 뒤 재확인합니다.")
                else:
                    # 타이머 진행 중
                    if current_time - pending_fire_check_time >= FIRE_CHECK_DELAY:
                        # 10초 경과 후에도 화재가 감지됨 -> 확정
                        print(f"--- 화재 확정. Gemini 분석 및 모니터링 시작 ---")
                        is_monitoring_fire = True
                        pending_fire_check_time = None
                        
                        # 즉시 Gemini 호출
                        last_gemini_check_time = current_time
                        cv2.imshow("Gemini Snapshot", frame)
                        threading.Thread(target=run_gemini_analysis_thread, args=(frame.copy(),)).start()
            else:
                # Case 2: 이미 모니터링 중 (10분마다 재확인)
                if current_time - last_gemini_check_time > GEMINI_CHECK_INTERVAL:
                    print(f"--- 화재 모니터링 업데이트 (10분 경과) ---")
                    last_gemini_check_time = current_time
                    
                    cv2.imshow("Gemini Snapshot", frame)
                    threading.Thread(target=run_gemini_analysis_thread, args=(frame.copy(),)).start()
                
                # 모니터링 중에는 pending 타이머 불필요
                pending_fire_check_time = None

        else:
            # 현재 프레임에서 화재 없음
            if pending_fire_check_time is not None:
                # 재확인 대기 중이었는데 화재가 사라짐 -> 취소
                print(f"재확인 중 화재 소실. 대기 취소.")
                pending_fire_check_time = None

        # 3-2. 동물 감지 결과 분석 (스킵된 프레임에서만)
        if animal_results is not None:
            for r in animal_results:
                boxes = r.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    class_name = animal_model.names[cls_id]

                    # 동물 클래스 확인
                    if class_name.lower() in [c.lower() for c in ANIMAL_CLASSES]:
                        animal_detected_in_frame = True
                        detected_animals.append(class_name)
                        
                        x1, y1, x2, y2 = box.xyxy[0]
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # 동물 감지: 초록색 박스
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        confidence = math.ceil(box.conf[0] * 100) / 100
                        label = f"{class_name.upper()} {confidence}"
                        cv2.putText(frame, label, (x1, y1 - 10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 4. 프레임을 연결된 클라이언트로 송신
        if client_socket:
            try:
                # JPEG로 압축
                ret_encode, frame_encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                data = frame_encoded.tobytes()
                
                # 프레임 크기와 데이터 전송
                frame_size = len(data)
                client_socket.sendall(frame_size.to_bytes(4, byteorder='big'))
                client_socket.sendall(data)
            except (BrokenPipeError, ConnectionResetError):
                print("클라이언트 연결 해제됨")
                client_socket = None
            except Exception as e:
                print(f"송신 오류: {e}")
                client_socket = None
        
        if websocket_connected:
            send_frame_via_websocket(frame)

        # 5. 화재 감지 여부 및 알림 로직
        current_time = time.time()
        
        # === 화재 감지 처리 ===
        if fire_detected_in_frame:
            # 로그 출력 간격 확인
            if current_time - last_fire_log_time >= FIRE_LOG_INTERVAL:
                last_fire_log_time = current_time
                print(f"[{time.ctime()}] 🔥 화재 감지 !!!")
                
                fire_event_data = {
                    "event_type": "fire_detected",
                    "timestamp": datetime.now().isoformat(),
                    "unix_timestamp": current_time,
                    "confidence": max_fire_confidence,
                    "message": "🔥 화재가 감지되었습니다!"
                }
                
                try:
                    with open(FIRE_EVENT_LOG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(fire_event_data, f, indent=2, ensure_ascii=False)
                except Exception as e:
                    print(f"화재 이벤트 저장 오류: {e}")
            
            if (current_time - last_alert_time) > ALERT_COOLDOWN:
                print(">>> 화재 알림 조건 충족!")
                last_alert_time = current_time
        
        # === 동물 감지 처리 ===
        if animal_detected_in_frame:
            animal_list = ", ".join(set(detected_animals))  # 중복 제거
            print(f"[{time.ctime()}] 🐾 동물 감지: {animal_list}")
            
            animal_event_data = {
                "event_type": "animal_detected",
                "timestamp": datetime.now().isoformat(),
                "unix_timestamp": current_time,
                "detected_animals": detected_animals,
                "message": f"🐾 {animal_list}이(가) 감지되었습니다!"
            }
            
            try:
                with open(ANIMAL_EVENT_LOG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(animal_event_data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"동물 이벤트 저장 오류: {e}")

        # GUI 이벤트 처리를 위해 waitKey 사용 (30ms 대기)
        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n시스템 종료 중...")

finally:
    if client_socket:
        client_socket.close()
    server_socket.close()
    cap.release()
    cv2.destroyAllWindows()
    print("--- 감지 시스템을 종료합니다. ---")