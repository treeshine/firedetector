"""
카메라 페이지 (좌측)
"""

import streamlit as st
import queue
from helpers import frame_queue, connection_status, start_receiver_thread, debug_log

debug_log("camera.py 페이지 로드")

st.header("📷 실시간 카메라 화면")

# 백그라운드 스레드 시작
start_receiver_thread()

debug_log("camera.py - placeholder 생성")

# Placeholder 생성
camera_placeholder = st.empty()
status_placeholder = st.empty()

frame_count = 0

# 프레임 표시 루프
while True:
    try:
        frame = frame_queue.get(timeout=0.1)
        camera_placeholder.image(frame, width="stretch")
        status_placeholder.success(connection_status["status"])
        frame_count += 1
        if frame_count % 30 == 0:
            debug_log(f"[카메라] 프레임 표시: {frame_count}개")
    except queue.Empty:
        status_placeholder.warning("⏳ 프레임 대기 중...")
    except Exception as e:
        status_placeholder.error(f"⚠️ 표시 오류: {e}")
        debug_log(f"카메라 오류: {e}")
        break
