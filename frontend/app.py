"""
🔥 화재 감지 시스템 - 메인 진입점
Multi-Page Streamlit 앱
"""

import streamlit as st
from helpers import start_receiver_thread, debug_log, check_fire_event

# 페이지 설정
st.set_page_config(
    page_title="Fire Detection System",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

debug_log("========== 메인 홈 페이지 로드 ==========")

st.title("🔥 화재 감지 모니터링 시스템")

# 백그라운드 스레드 시작
start_receiver_thread()

# 최상단: 경고 영역
alert_placeholder = st.empty()

# 경고 확인
fire_event = check_fire_event()
if fire_event:
    with alert_placeholder.container():
        st.error(f"""
        ### 🚨 화재 감지 경고! 🚨
        
        **감지 시간**: {fire_event.get("timestamp", "N/A")}  
        **신뢰도**: {fire_event.get("confidence", "N/A")}  
        
        ⚠️ 즉시 현장을 확인하고 필요시 119에 신고하세요!
        """)

st.markdown("""
---
### 📌 메뉴 안내

좌측 사이드바에서 선택하세요:
- **📷 Dashboard**: 카메라 + 대시보드 통합 보기
- **⚙️ Settings**: 시스템 설정

---
""")

st.info("✅ 시스템 준비 완료. 왼쪽 메뉴에서 페이지를 선택하세요.")

debug_log("메인 홈 페이지 로드 완료")
