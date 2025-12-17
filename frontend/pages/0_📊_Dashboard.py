"""
대시보드 페이지 (State Machine 기반 화재 감지)
수정 사항:
- State Machine (Rising/Falling Edge 감지)으로 정확한 이벤트 카운트
- 두 개의 시계: 큰 시계(지속 시간), 작은 시계(마지막 감지 T- 형태)
- threshold 10초로 증가: YOLO 감지 끊김 방지
- T- 형태: 마지막 감지 시각과 경과 시간 표시
"""

import streamlit as st
import queue
import time
from datetime import datetime, timedelta
from helpers import (
    frame_queue,
    connection_status,
    start_receiver_thread,
    debug_log,
    check_fire_event,
    is_fire_active,
)

st.set_page_config(page_title="Fire Dashboard", layout="wide")

debug_log("========== 대시보드 페이지 로드 ==========")
st.header("📊 실시간 화재 감지 대시보드")

# 백그라운드 스레드 시작
start_receiver_thread()

# --- 1. 레이아웃 구성 ---
alert_placeholder = st.empty()
col_left, col_right = st.columns([1.5, 1])

with col_left:
    with st.container(border=True):
        st.subheader("📷 실시간 모니터링")
        camera_placeholder = st.empty()
        connection_info = st.empty()

with col_right:
    # 카드 1: 화재 지속 시간
    with st.container(border=True):
        st.subheader("⏱ 화재 시간 모니터링")
        duration_metric = st.empty()  # 큰 시계
        last_detect_text = st.empty()  # 작은 시계 (T- 형태)

    # 카드 2: 이벤트 빈도
    with st.container(border=True):
        st.subheader("📈 감지 횟수")
        freq_metric = st.empty()

    # 카드 3: 현재 상태
    with st.container(border=True):
        st.subheader("✅ 시스템 상태")
        status_indicator = st.empty()

    # 카드 4: Gemini 분석 결과
    with st.container(border=True):
        st.subheader("🤖 Gemini AI 분석")
        gemini_metric = st.empty()

# --- 2. 상태 변수 초기화 ---
if "app_start_time" not in st.session_state:
    st.session_state["app_start_time"] = datetime.now()

fire_start_time = None  # 화재가 처음 감지된 시각
daily_fire_count = 0  # 오늘 발생한 화재 건수
was_fire_active = False  # 직전 루프에서의 화재 상태
fire_end_time = None  # 화재 종료 시각 (Falling Edge)
FALLBACK_DURATION = 10  # 화재 종료 후 유지 시간 (초)

# 초기 렌더링
duration_metric.metric(label="현재 지속 시간", value="00:00:00", delta="대기 중")
freq_metric.metric(label="누적 감지 횟수", value="0 회")
status_indicator.success("정상 (Safe)")
last_detect_text.markdown("🕒 **마지막 감지:** -")

debug_log("대시보드 - 루프 진입")
frame_count = 0

# --- 3. 메인 루프 ---
while True:
    # A. 데이터 읽기 (매번 현재 JSON 상태 체크)
    # JSON 파일을 직접 읽어서 현재 상태 확인 (중복 방지 로직 우회)
    event_data = None
    try:
        import os
        import json

        if os.path.exists("fire_events.json"):
            with open("fire_events.json", "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    event_data = json.loads(content)
    except:
        pass

    # Gemini 로그 읽기
    gemini_msg = "**마지막 탐색 시간: -**\n\n시스템 가동됨"
    try:
        if os.path.exists("gemini_analysis_log.txt"):
            with open("gemini_analysis_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_line = lines[-1].strip()
                    # Parse: [Timestamp] Gemini 분석 결과: Message
                    if "] Gemini 분석 결과: " in last_line:
                        parts = last_line.split("] Gemini 분석 결과: ")
                        if len(parts) > 1:
                            timestamp_str = parts[0].replace("[", "")
                            message = parts[1]

                            try:
                                log_dt = datetime.strptime(
                                    timestamp_str, "%Y-%m-%d %H:%M:%S"
                                )
                                # 앱 시작 이후의 로그만 표시
                                if (
                                    "app_start_time" in st.session_state
                                    and log_dt > st.session_state["app_start_time"]
                                ):
                                    gemini_msg = f"**[{timestamp_str}]**\n\n{message}"
                            except:
                                pass
    except Exception as e:
        gemini_msg = f"로그 읽기 오류: {e}"

    gemini_metric.markdown(gemini_msg)

    now = datetime.now()

    # [중요] threshold를 10초로 설정
    # YOLO 감지가 끊겨도 10초 이내에 갱신되면 화재 상태 유지
    current_active = is_fire_active(event_data, threshold_seconds=10)

    # B. 상태 머신 (State Machine)

    # [Rising Edge] 화재 시작
    if current_active and not was_fire_active:
        fire_start_time = now
        daily_fire_count += 1
        debug_log("🔥 화재 시작! 타이머 가동")

    # [Falling Edge] 화재 종료 (현재 비활성 & 이전 활성)
    if not current_active and was_fire_active:
        fire_start_time = None
        fire_end_time = now  # ← 종료 시각 기록
        alert_placeholder.empty()
        duration_metric.metric(
            label="현재 지속 시간", value="00:00:00", delta_color="off"
        )
        # 마지막 감지 시간은 보존 (업데이트하지 않음)
        debug_log("✅ 화재 종료. 카운다운 시작")

    # C. Falling Edge 카운다운 상태 (화재 사라졌지만 10초 유지)
    elif not current_active and fire_end_time is not None:
        fallback_elapsed = (now - fire_end_time).total_seconds()

        if fallback_elapsed < FALLBACK_DURATION:
            # 카운다운 중 (10초 ~ 0초)
            countdown_sec = int(FALLBACK_DURATION - fallback_elapsed)
            status_indicator.warning(f"🟡 화재 감소됨 (T - {countdown_sec}s)")
            duration_metric.metric(
                label="카운다운", value=f"T - {countdown_sec}s", delta="감소 중"
            )
        else:
            # 카운다운 완료 → 정상 상태
            fire_end_time = None
            status_indicator.success("정상 (Safe)")
            duration_metric.metric(
                label="현재 지속 시간", value="00:00:00", delta_color="off"
            )
            debug_log("✅ 카운다운 완료. 정상 상태 복귀")

    else:
        # 정상 상태 (이벤트 없음)
        status_indicator.success("정상 (Safe)")

    # D. UI 업데이트 (화재 상태일 때)
    if current_active:
        # 1. 큰 시계 (지속 시간)
        if fire_start_time:
            elapsed = now - fire_start_time
            # 마이크로초 제거하여 깔끔하게 표시 (0:00:12)
            elapsed_str = str(elapsed).split(".")[0]
            # 0으로 시작하면 00으로 패딩 (선택 사항)
            if len(elapsed_str) == 7:
                elapsed_str = "0" + elapsed_str
            duration_metric.metric(
                label="🔥 화재 지속 중", value=elapsed_str, delta="DANGER"
            )

        # 2. 작은 시계 (T- 형태 적용)
        if event_data:
            ts = event_data.get("timestamp", "")
            try:
                # ISO 포맷 파싱
                event_dt = datetime.fromisoformat(ts)

                # 절대 시간 (예: 12:34:56)
                abs_time = event_dt.strftime("%H:%M:%S")

                # 상대 시간 차이 계산 (현재 - 감지시각)
                diff = now - event_dt
                diff_sec = int(diff.total_seconds())

                # [수정된 부분] "시간 (T - 초)" 형태로 표시
                display_text = f"**🕒 마지막 감지:** {abs_time} (T - {diff_sec}s)"
                last_detect_text.markdown(display_text)

            except Exception as e:
                # 파싱 실패 시 원본 표시
                debug_log(f"시간 파싱 오류: {e}")
                last_detect_text.caption(f"마지막 감지: {ts}")

        # 3. 상태 표시
        status_indicator.error("🚨 화재 발생 (DANGER)")
        with alert_placeholder.container():
            st.error(
                f"🚨 **화재 감지됨!** (신뢰도: {event_data.get('confidence', 0):.2f})"
            )

    # E. 공통 업데이트
    freq_metric.metric(label="누적 감지 횟수", value=f"{daily_fire_count} 회")
    was_fire_active = current_active

    # F. 카메라 프레임 업데이트
    try:
        frame = frame_queue.get(timeout=0.1)
        camera_placeholder.image(frame, width="stretch")
        connection_info.info(f"연결 상태: {connection_status['status']}")

        frame_count += 1
        if frame_count % 30 == 0:
            pass

    except queue.Empty:
        pass
    except Exception as e:
        connection_info.error(f"영상 오류: {e}")
        time.sleep(0.1)
