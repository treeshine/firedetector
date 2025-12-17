"""
공용 헬퍼 함수 및 상수
"""
import queue
import threading
import socket
import cv2
import numpy as np
import time
import sys
import json
import os
from datetime import datetime

# 전역 설정
HOST = 'localhost'
PORT = 5005
QUEUE_SIZE = 2
EVENT_LOG_FILE = "fire_events.json"
FIRE_ACTIVE_THRESHOLD = 30  # 화재 활성 판정 임계값 (초)

# 전역 프레임 큐
frame_queue = queue.Queue(maxsize=QUEUE_SIZE)
connection_status = {"status": "연결 중..."}
receiver_thread_ref = {"thread": None}
last_event_id = {"id": None}  # 마지막으로 처리한 이벤트 ID

def debug_log(msg):
    """디버그 로그 출력 (타임스탬프 포함)"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DEBUG {timestamp}] {msg}", file=sys.stderr, flush=True)

def receive_frames():
    """프레임 수신 함수 (백그라운드 스레드에서 실행)"""
    debug_log("receive_frames 함수 시작")
    
    while True:
        try:
            debug_log(f"소켓 연결 시도: {HOST}:{PORT}")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((HOST, PORT))
            connection_status["status"] = "✓ 연결됨"
            debug_log("소켓 연결 성공")
            
            while True:
                try:
                    # 프레임 크기 수신 (4 바이트)
                    frame_size_data = client_socket.recv(4)
                    if not frame_size_data:
                        connection_status["status"] = "⚠️ 연결 끊김"
                        debug_log("연결 끊어짐")
                        break
                    
                    frame_size = int.from_bytes(frame_size_data, byteorder='big')
                    debug_log(f"프레임 크기: {frame_size} bytes")
                    
                    # 프레임 데이터 수신
                    frame_data = b''
                    while len(frame_data) < frame_size:
                        chunk = client_socket.recv(min(4096, frame_size - len(frame_data)))
                        if not chunk:
                            break
                        frame_data += chunk
                    
                    # JPEG 디코딩
                    frame_array = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                    
                    if frame is not None:
                        # BGR을 RGB로 변환
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # 큐에 프레임 추가
                        try:
                            frame_queue.get_nowait()
                        except queue.Empty:
                            pass
                        frame_queue.put(frame_rgb)
                        connection_status["status"] = "✓ 연결됨"
                    
                except Exception as e:
                    error_msg = str(e)[:30]
                    connection_status["status"] = f"⚠️ 오류: {error_msg}"
                    debug_log(f"프레임 수신 오류: {error_msg}")
                    break
        
        except ConnectionRefusedError:
            connection_status["status"] = "❌ 서버 연결 불가"
            debug_log("서버 연결 거부됨, 2초 후 재시도")
            time.sleep(2)
        except Exception as e:
            error_msg = str(e)[:30]
            connection_status["status"] = f"❌ 오류: {error_msg}"
            debug_log(f"예외 발생: {error_msg}")
            time.sleep(2)

def start_receiver_thread():
    """백그라운드 스레드 시작"""
    if receiver_thread_ref["thread"] is None or not receiver_thread_ref["thread"].is_alive():
        debug_log("백그라운드 스레드 시작")
        receiver_thread = threading.Thread(target=receive_frames, daemon=True)
        receiver_thread.start()
        receiver_thread_ref["thread"] = receiver_thread
        debug_log("백그라운드 스레드 실행 중")

def check_fire_event():
    """
    화재 감지 이벤트 확인
    새로운 이벤트가 있으면 반환, 없으면 None 반환
    """
    try:
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return None
                event_data = json.loads(content)
            
            if not isinstance(event_data, dict):
                return None
            
            # 새로운 이벤트인지 확인 (같은 이벤트 중복 방지)
            event_id = event_data.get("unix_timestamp")
            if event_id != last_event_id["id"]:
                last_event_id["id"] = event_id
                debug_log(f"🔥 새로운 화재 감지 이벤트: {event_data.get('timestamp')}")
                return event_data
    except json.JSONDecodeError as e:
        debug_log(f"이벤트 파일 - JSON 파싱 오류: {e}")
    except Exception as e:
        debug_log(f"이벤트 파일 읽기 오류: {e}")
    
    return None

def get_fire_events_history():
    """
    이벤트 로그 파일에서 모든 화재 이벤트 반환
    """
    try:
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, 'r') as f:
                event_data = json.load(f)
            
            # 단일 이벤트 또는 리스트 형식 처리
            if isinstance(event_data, list):
                return event_data
            else:
                return [event_data]
    except Exception as e:
        debug_log(f"이벤트 히스토리 읽기 오류: {e}")
    
    return []

def get_fire_duration():
    """
    화재 지속 시간 계산 (가장 최근 이벤트부터 현재까지)
    포맷: "HH:MM:SS"
    """
    try:
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return "00:00:00", 0
                event_data = json.loads(content)
            
            if event_data and isinstance(event_data, dict) and "unix_timestamp" in event_data:
                start_time = event_data["unix_timestamp"]
                current_time = time.time()
                duration_seconds = int(current_time - start_time)
                
                hours = duration_seconds // 3600
                minutes = (duration_seconds % 3600) // 60
                seconds = duration_seconds % 60
                
                time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                return time_str, duration_seconds
    except json.JSONDecodeError as e:
        debug_log(f"화재 지속 시간 - JSON 파싱 오류: {e}")
    except Exception as e:
        debug_log(f"화재 지속 시간 계산 오류: {e}")
    
    return "00:00:00", 0

def get_fire_event_frequency():
    """
    최근 1시간 내 화재 이벤트 발생 빈도 계산
    """
    try:
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return 0
                event_data = json.loads(content)
            
            if event_data and isinstance(event_data, dict) and "unix_timestamp" in event_data:
                event_time = event_data["unix_timestamp"]
                current_time = time.time()
                one_hour_ago = current_time - 3600  # 1시간 = 3600초
                
                # 지난 1시간 이내의 이벤트 카운트
                if event_time >= one_hour_ago:
                    return 1  # 현재 활성 이벤트
                else:
                    return 0  # 1시간 이상 이전 이벤트
    except json.JSONDecodeError as e:
        debug_log(f"이벤트 빈도 - JSON 파싱 오류: {e}")
    except Exception as e:
        debug_log(f"이벤트 빈도 계산 오류: {e}")
    
    return 0

def get_fire_status():
    """
    현재 화재 상태 반환
    "정상 (Normal)" 또는 "화재 감지 (Fire Detected)"
    """
    try:
        if os.path.exists(EVENT_LOG_FILE):
            with open(EVENT_LOG_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return "🟢 정상 (Normal)"
                event_data = json.loads(content)
            
            if event_data and isinstance(event_data, dict):
                event_time = event_data.get("unix_timestamp")
                current_time = time.time()
                
                # 30초 이내의 이벤트면 활성 상태
                if event_time and (current_time - event_time) < 30:
                    return "🔴 화재 감지 (Fire Detected)"
                else:
                    return "🟢 정상 (Normal)"
    except json.JSONDecodeError as e:
        debug_log(f"상태 확인 - JSON 파싱 오류: {e}")
    except Exception as e:
        debug_log(f"상태 확인 오류: {e}")
    
    return "🟢 정상 (Normal)"

def is_fire_active(event_data, threshold_seconds=None):
    """
    이벤트 데이터가 '현재 유효한 화재'인지 판단합니다.
    기준: 현재 시간과 감지 시간의 차이가 임계값 이내여야 함.
    
    Args:
        event_data: JSON에서 읽은 이벤트 데이터 딕셔너리
        threshold_seconds: 임계값 (초). None이면 FIRE_ACTIVE_THRESHOLD 사용
    
    Returns:
        bool: 현재 활성 화재면 True, 아니면 False
    """
    if threshold_seconds is None:
        threshold_seconds = FIRE_ACTIVE_THRESHOLD
    
    if not event_data or 'timestamp' not in event_data:
        return False
    
    try:
        # timestamp 형식이 ISO 포맷이라고 가정 (예: '2025-11-28T00:04:03.571316')
        event_time = datetime.fromisoformat(event_data['timestamp'])
        time_diff = datetime.now() - event_time
        
        # 임계값 이내에 갱신된 데이터만 '현재 화재'로 인정
        return time_diff.total_seconds() <= threshold_seconds
    except Exception as e:
        debug_log(f"화재 활성 판정 오류 (형식 확인 필요): {e}")
        return False
