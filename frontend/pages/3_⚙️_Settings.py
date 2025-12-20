"""
설정 페이지
"""

import os
import streamlit as st
from helpers import start_receiver_thread, debug_log

debug_log("settings.py 페이지 로드")

st.header("⚙️ 설정")

# 백그라운드 스레드 시작
start_receiver_thread()

st.markdown("---")

# 감지 설정
st.subheader("🔥 화재 감지 설정")
confidence_threshold = st.slider("신뢰도 임계값", 0.0, 1.0, 0.5, 0.05)
alert_cooldown = st.slider("알림 쿨다운 (초)", 10, 300, 30, 10)

st.write(f"현재 신뢰도 임계값: {confidence_threshold:.2f}")
st.write(f"현재 알림 쿨다운: {alert_cooldown}초")

st.markdown("---")

# 시스템 정보
st.subheader("ℹ️ 시스템 정보")
st.info(f"""
- **백엔드**: YOLO 화재 감지, FastAPI 백업 서버
- **호스트**: {os.getenv("YOLO_SERVER")}(YOLO), {os.getenv("FASTAPI_SERVER")}(FastAPI)
""")

st.markdown("---")

st.success("설정 페이지가 정상 작동합니다.")
debug_log("settings.py - 페이지 생성 완료")
