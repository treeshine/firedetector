"""
공용 헬퍼 함수 및 상수

TCP 기반 타입 프로토콜: 
 [4 bytes: size of payload][1 byte: type][payload]
 - 0x01: 이미지 프레임(JPEG)
 - 0x02: 동물 이벤트 (JSON)
 - 0x03: 동물 이벤트 (JSON)
 - 0x04: Gemini 분석 결과 (JSON)
"""
import json
import os
import queue
import socket
import sys
import threading
import time
from datetime import datetime

import cv2
import numpy as np

# 메시지 타입 상수
MSG_TYPE_FRAME = 0x01
MSG_TYPE_FIRE_EVENT = 0x02
MSG_TYPE_ANIMAL_EVENT = 0x03
MSG_TYPE_GEMINI_RESULT = 0x04

# 전역 설정
HOST = "localhost"
PORT = 5005
QUEUE_SIZE = 2
FIRE_ACTIVE_THRESHOLD = 30  # 화재 활성 판정 임계값 (초)

# 전역 프레임 큐
frame_queue = queue.Queue(maxsize=QUEUE_SIZE)
connection_status = {"status": "연결 중..."}
receiver_thread_ref = {"thread": None}

# --- TCP로 수신한 이벤트 데이터 저(thread-safe) ---
_data_lock = threading.Lock()
_latest_fire_event = None
_latest_animal_event = None
_latest_gemini_result = None


def debug_log(msg):
    """디버그 로그 출력 (타임스탬프 포함)"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[DEBUG {timestamp}] {msg}", file=sys.stderr, flush=True)


def _recv_n_bytes(sock, n):
    """정확히 n바이트 수신"""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("연결 종료됨")
        data += chunk
    return data


def _process_frame(payload):
    """이미지 프레임 처리"""
    try:
        frame_array = np.frombuffer(payload, dtype=np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                frame_queue.get_nowait()
            except queue.Empty:
                pass
            frame_queue.put(frame_rgb)
            connection_status["status"] = "✓ 연결됨"
            debug_log("소켓 연결 성공")
    except Exception as e:
        debug_log(f"프레 처리 오류: {e}")


def _process_fire_event(payload):
    """화재 이벤트 처리"""
    global _latest_fire_event
    try:
        event_data = json.loads(payload.decode("utf-8"))
        with _data_lock:
            _latest_fire_event = event_data

        debug_log(f"🔥 화재 이벤트 수신: conf={event_data.get('confidence', 0):.2f}")
    except Exception as e:
        debug_log(f"화재 이벤트 처리 오류: {e}")


def _process_animal_evnet(payload):
    """동물 이벤트 처리"""
    global _latest_animal_event
    try:
        event_data = json.loads(payload.decode("utf-8"))
        with _data_lock:
            _latest_animal_event = event_data
        animals = event_data.get("detected_animals", [])
        debug_log(f"🐾 동물 이벤트 수신: {', '.join(animals)}")
    except Exception as e:
        debug_log(f"동물 이벤트 처리 오류: {e}")


def _process_gemini_result(payload):
    global _latest_gemini_result
    try:
        result_data = json.loads(payload.decode("utf-8"))
        with _data_lock:
            _latest_gemini_result = result_data
        debug_log(f"🤖 Gemini 결과 수신: {result_data.get('result', '')[:50]}...")
    except Exception as e:
        debug_log(f"Gemini 결과 처리 오류: {e}")


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
                    # 프레임 크기 수신 (4 + 1(size + type) 바이트)
                    header = _recv_n_bytes(client_socket, 5)
                    payload_size = struct.unpack(">I", header[:4][0])
                    msg_type = header[4]

                    # payload 수신
                    payload = _recv_n_bytes(client_socket, payload_size)

                    if msg_type == MSG_TYPE_FRAME:
                        _process_frame(payload)
                    elif msg_type == MSG_TYPE_FIRE_EVENT:
                        _process_fire_event(payload)
                    elif msg_type == MSG_TYPE_ANIMAL_EVENT:
                        _process_animal_evnet(payload)
                    elif msg_type == MSG_TYPE_GEMINI_RESULT:
                        _process_gemini_result(payload)
                    else:
                        debug_log(f"알 수 없는 메시지 타입: {msg_type}")

                except ConnectionError:
                    connection_status["status"] = "⚠️ 연결 끊김"
                    debug_log("연결 끊어짐")
                    break
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
    if (
        receiver_thread_ref["thread"] is None
        or not receiver_thread_ref["thread"].is_alive()
    ):
        debug_log("백그라운드 스레드 시작")
        receiver_thread = threading.Thread(target=receive_frames, daemon=True)
        receiver_thread.start()
        receiver_thread_ref["thread"] = receiver_thread
        debug_log("백그라운드 스레드 실행 중")


# 수신한 이벤트 데이터 접근
def get_latest_fire_event():
    """최신 화재 이벤트 반환 (TCP 수신 데이터)"""
    with _data_lock:
        return _latest_fire_event.copy() if _latest_fire_event else None


def get_latest_animal_event():
    """최신 동물 이벤트 반환 (TCP 수신 데이터)"""
    with _data_lock:
        return _latest_animal_event.copy() if _latest_animal_event else None


def get_latest_gemini_result():
    """최신 Gemini 분석 결과 반환(TCP 수신 데이터)"""
    with _data_lock:
        return _latest_gemini_result.copy() if _latest_gemini_result else None


def check_fire_event():
    """화재 감지 이벤트 확인"""
    return get_latest_fire_event()


def get_fire_duration():
    """
    화재 지속 시간 계산 (가장 최근 이벤트부터 현재까지)
    포맷: "HH:MM:SS"
    """

    event_data = get_latest_fire_event()
    if event_data and "unix_timestamp" in event_data:
        try:
            start_time = event_data["unix_timestamp"]
            current_time = time.time()
            duration_seconds = int(current_time - start_time)

            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60

            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return time_str, duration_seconds

        except Exception as e:
            debug_log(f"화재 지속 시간 계산 오류: {e}")

    return "00:00:00", 0


def get_fire_status():
    """
    현재 화재 상태 반환
    "정상 (Normal)" 또는 "화재 감지 (Fire Detected)"
    """

    if is_fire_active():
        return "🔴 화재 감지 (Fire Detected)"
    return "🟢 정상 (Normal)"


def is_fire_active(event_data=None, threshold_seconds=None):
    """
    이벤트 데이터가 '현재 유효한 화재'인지 판단합니다.
    기준: 현재 시간과 감지 시간의 차이가 임계값 이내여야 함.

    Args:
        event_data: 이벤트 데이터 딕셔너리
        threshold_seconds: 임계값 (초). None이면 FIRE_ACTIVE_THRESHOLD 사용

    Returns:
        bool: 현재 활성 화재면 True, 아니면 False
    """

    if threshold_seconds is None:
        threshold_seconds = FIRE_ACTIVE_THRESHOLD
    if event_data is None:
        event_data = get_latest_fire_event()
    if not event_data:
        return False

    if "unix_timestamp" in event_data:
        try:
            event_time = event_data["unix_timestamp"]
            time_diff = time.time() - event_time
            return time_diff <= threshold_seconds

        except Exception as e:
            debug_log(f"화재 활성 판정 오류(unix_timestam): {e}")

    return False
