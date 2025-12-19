"""
대시보드 페이지 (TCP 기반 메트릭 수신)
- 파일 기반 → TCP 기반으로 변경
- helpers.py의 get_latest_* 함수 사용
"""

import streamlit as st
import queue
import time
from datetime import datetime
from helpers import (
    frame_queue,
    connection_status,
    start_receiver_thread,
    debug_log,
    get_latest_fire_event,
    get_latest_animal_event,
    get_latest_gemini_result,
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
        duration_metric = st.empty()
        last_detect_text = st.empty()

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

    # 카드 5: 동물 감지 (새로 추가)
    with st.container(border=True):
        st.subheader("🐾 동물 감지")
        animal_metric = st.empty()

# --- 2. 상태 변수 초기화 ---
if "app_start_time" not in st.session_state:
    st.session_state["app_start_time"] = datetime.now()

fire_start_time = None
daily_fire_count = 0
was_fire_active = False
fire_end_time = None
FALLBACK_DURATION = 10

# 초기 렌더링
duration_metric.metric(label="현재 지속 시간", value="00:00:00", delta="대기 중")
freq_metric.metric(label="누적 감지 횟수", value="0 회")
status_indicator.success("정상 (Safe)")
last_detect_text.markdown("🕒 **마지막 감지:** -")
animal_metric.markdown("감지된 동물 없음")

debug_log("대시보드 - 루프 진입")
frame_count = 0

# --- 3. 메인 루프 ---
while True:
    now = datetime.now()

    # A. TCP로 받은 이벤트 데이터 가져오기
    event_data = get_latest_fire_event()
    animal_data = get_latest_animal_event()
    gemini_data = get_latest_gemini_result()

    # B. Gemini 결과 표시
    if gemini_data:
        timestamp = gemini_data.get("timestamp", "")
        result = gemini_data.get("result", "")
        try:
            ts_dt = datetime.fromisoformat(timestamp)
            if ts_dt > st.session_state["app_start_time"]:
                ts_str = ts_dt.strftime("%Y-%m-%d %H:%M:%S")
                gemini_metric.markdown(f"**[{ts_str}]**\n\n{result}")
        except:
            gemini_metric.markdown(f"{result}")
    else:
        gemini_metric.markdown("**마지막 탐색 시간: -**\n\n시스템 가동됨")

    # C. 동물 감지 표시
    if animal_data:
        animals = animal_data.get("detected_animals", [])
        timestamp = animal_data.get("timestamp", "")
        if animals:
            animal_list = ", ".join(set(animals))
            try:
                ts_dt = datetime.fromisoformat(timestamp)
                ts_str = ts_dt.strftime("%H:%M:%S")
                animal_metric.markdown(f"**{animal_list}** (마지막: {ts_str})")
            except:
                animal_metric.markdown(f"**{animal_list}**")
    else:
        animal_metric.markdown("감지된 동물 없음")

    # D. 화재 상태 확인 (threshold 10초)
    current_active = is_fire_active(event_data, threshold_seconds=10)

    # [Rising Edge] 화재 시작
    if current_active and not was_fire_active:
        fire_start_time = now
        daily_fire_count += 1
        debug_log("🔥 화재 시작! 타이머 가동")

    # [Falling Edge] 화재 종료
    if not current_active and was_fire_active:
        fire_start_time = None
        fire_end_time = now
        alert_placeholder.empty()
        duration_metric.metric(
            label="현재 지속 시간", value="00:00:00", delta_color="off"
        )
        debug_log("✅ 화재 종료. 카운다운 시작")

    # E. Falling Edge 카운다운 상태
    elif not current_active and fire_end_time is not None:
        fallback_elapsed = (now - fire_end_time).total_seconds()

        if fallback_elapsed < FALLBACK_DURATION:
            countdown_sec = int(FALLBACK_DURATION - fallback_elapsed)
            status_indicator.warning(f"🟡 화재 감소됨 (T - {countdown_sec}s)")
            duration_metric.metric(
                label="카운다운", value=f"T - {countdown_sec}s", delta="감소 중"
            )
        else:
            fire_end_time = None
            status_indicator.success("정상 (Safe)")
            duration_metric.metric(
                label="현재 지속 시간", value="00:00:00", delta_color="off"
            )
            debug_log("✅ 카운다운 완료. 정상 상태 복귀")

    else:
        if not current_active:
            status_indicator.success("정상 (Safe)")

    # F. UI 업데이트 (화재 상태일 때)
    if current_active:
        # 1. 큰 시계 (지속 시간)
        if fire_start_time:
            elapsed = now - fire_start_time
            elapsed_str = str(elapsed).split(".")[0]
            if len(elapsed_str) == 7:
                elapsed_str = "0" + elapsed_str
            duration_metric.metric(
                label="🔥 화재 지속 중", value=elapsed_str, delta="DANGER"
            )

        # 2. 작은 시계 (T- 형태)
        if event_data:
            ts = event_data.get("timestamp", "")
            try:
                event_dt = datetime.fromisoformat(ts)
                abs_time = event_dt.strftime("%H:%M:%S")
                diff = now - event_dt
                diff_sec = int(diff.total_seconds())
                display_text = f"**🕒 마지막 감지:** {abs_time} (T - {diff_sec}s)"
                last_detect_text.markdown(display_text)
            except Exception as e:
                debug_log(f"시간 파싱 오류: {e}")
                last_detect_text.caption(f"마지막 감지: {ts}")

        # 3. 상태 표시
        status_indicator.error("🚨 화재 발생 (DANGER)")
        with alert_placeholder.container():
            st.error(
                f"🚨 **화재 감지됨!** (신뢰도: {event_data.get('confidence', 0):.2f})"
            )

    # G. 공통 업데이트
    freq_metric.metric(label="누적 감지 횟수", value=f"{daily_fire_count} 회")
    was_fire_active = current_active

    # H. 카메라 프레임 업데이트
    try:
        frame = frame_queue.get(timeout=0.1)
        camera_placeholder.image(frame, use_container_width=True)
        connection_info.info(f"연결 상태: {connection_status['status']}")

        frame_count += 1

    except queue.Empty:
        pass
    except Exception as e:
        connection_info.error(f"영상 오류: {e}")
        time.sleep(0.1)