"""
블랙박스 영상 관리 대시보드
- 백업 영상 목록 조회 및 재생
- 오탐(FP) 영상 목록 조회 및 재생
- 오탐 신고 기능
"""

import streamlit as st
import requests
from datetime import datetime

# ============================================
# 설정
# ============================================
API_BASE_URL = st.sidebar.text_input(
    "🔗 API 서버 주소",
    value=f"http://{os.getenv("FASTAPI_SERVER")}/api/v1",
    help="FastAPI 서버 주소를 입력하세요"
)

# ============================================
# 페이지 설정
# ============================================
st.set_page_config(
    page_title="블랙박스 영상 관리",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 커스텀 CSS
# ============================================
st.markdown("""
<style>
    /* 메인 컨테이너 */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* 카드 스타일 */
    .video-card {
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #3d3d5c;
        transition: transform 0.2s, box-shadow 0.2s;
    }
    
    .video-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    /* 헤더 스타일 */
    .dashboard-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
    }
    
    .dashboard-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .dashboard-header p {
        color: rgba(255,255,255,0.8);
        margin-top: 0.5rem;
    }
    
    /* 통계 카드 */
    .stat-card {
        background: #262640;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        border-left: 4px solid #667eea;
    }
    
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #667eea;
    }
    
    .stat-label {
        color: #a0a0b0;
        font-size: 0.9rem;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    /* 탭 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #262640;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
    
    /* 썸네일 컨테이너 */
    .thumbnail-container {
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 0.5rem;
    }
    
    /* 비디오 정보 */
    .video-info {
        font-size: 0.85rem;
        color: #a0a0b0;
    }
    
    /* 성공/에러 메시지 */
    .success-msg {
        background: linear-gradient(90deg, #00c853 0%, #00e676 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .error-msg {
        background: linear-gradient(90deg, #ff5252 0%, #ff1744 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================
# API 호출 함수들
# ============================================
@st.cache_data(ttl=30)
def fetch_backup_videos():
    """백업 영상 목록 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/videos/backup", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"백업 영상 목록을 불러오는데 실패했습니다: {e}")
        return []


@st.cache_data(ttl=30)
def fetch_fp_videos():
    """오탐 영상 목록 조회"""
    try:
        response = requests.get(f"{API_BASE_URL}/videos/fp", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"오탐 영상 목록을 불러오는데 실패했습니다: {e}")
        return []


def report_fp(video_id):
    """오탐 신고"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/fpreport/{video_id}", timeout=10)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"오탐 신고에 실패했습니다: {e}")
        return False


def get_thumbnail_url(video_id, video_type="backup"):
    """썸네일 URL 반환"""
    if video_type == "backup":
        return f"{API_BASE_URL}/thumbnail/backup/{video_id}"
    else:
        return f"{API_BASE_URL}/thumbnail/fp/{video_id}"


def get_video_url(video_id, video_type="backup"):
    """비디오 URL 반환"""
    if video_type == "backup":
        return f"{API_BASE_URL}/videos/backup/{video_id}"
    else:
        return f"{API_BASE_URL}/videos/fp/{video_id}"


# ============================================
# UI 컴포넌트
# ============================================
def render_header():
    """헤더 렌더링"""
    st.markdown("""
    <div class="dashboard-header">
        <h1>🎬 블랙박스 영상 관리</h1>
        <p>백업 영상 조회 및 오탐 관리 시스템</p>
    </div>
    """, unsafe_allow_html=True)


def render_stats(backup_count, fp_count):
    """통계 카드 렌더링"""
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📹 백업 영상",
            value=f"{backup_count}개",
            delta=None
        )

    with col2:
        st.metric(
            label="⚠️ 오탐 영상",
            value=f"{fp_count}개",
            delta=None
        )

    with col3:
        total = backup_count + fp_count
        st.metric(
            label="📊 전체 영상",
            value=f"{total}개",
            delta=None
        )


def render_video_card(video, video_type="backup"):
    """비디오 카드 렌더링"""
    video_id = video.get('id')
    video_name = video.get('name', '제목 없음')
    file_size = video.get('file_size')
    duration = video.get('duration', '알 수 없음')
    created_at = video.get('created_at')

    with st.container():
        col1, col2 = st.columns([1, 2])

        with col1:
            # 썸네일
            thumbnail_url = get_thumbnail_url(video_id, video_type)
            st.image(thumbnail_url, use_container_width=True)

        with col2:
            st.subheader(f"🎥 {video_name}")

            # 메타데이터
            meta_col1, meta_col2 = st.columns(2)
            with meta_col1:
                st.caption(f"📦 크기: {file_size}")
                st.caption(f"⏱️ 길이: {duration}")
            with meta_col2:
                st.caption(f"📅 생성: {created_at}")
                st.caption(f"🆔 ID: {video_id}")

            # 액션 버튼
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                video_url = get_video_url(video_id, video_type)
                st.link_button("▶️ 영상 보기", video_url, use_container_width=True)

            with btn_col2:
                if video_type == "backup":
                    if st.button(
                        "🚨 오탐 신고",
                        key=f"report_{video_id}",
                        use_container_width=True,
                        type="secondary"
                    ):
                        if report_fp(video_id):
                            st.success("✅ 오탐 신고가 완료되었습니다!")
                            st.cache_data.clear()
                            st.rerun()

        st.divider()


def render_video_grid(videos, video_type="backup"):
    """비디오 그리드 렌더링"""
    if not videos:
        st.info("📭 표시할 영상이 없습니다.")
        return

    # 검색/필터
    col1, col2 = st.columns([3, 1])
    with col1:
        search_query = st.text_input(
            "🔍 영상 검색",
            placeholder="영상 이름으로 검색...",
            key=f"search_{video_type}"
        )
    with col2:
        sort_option = st.selectbox(
            "정렬",
            ["최신순", "오래된순", "이름순", "크기순"],
            key=f"sort_{video_type}"
        )

    # 필터링
    filtered_videos = videos
    if search_query:
        filtered_videos = [
            v for v in videos
            if search_query.lower() in v.get('name', '').lower()
        ]

    # 정렬
    if sort_option == "최신순":
        filtered_videos = sorted(
            filtered_videos,
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
    elif sort_option == "오래된순":
        filtered_videos = sorted(
            filtered_videos,
            key=lambda x: x.get('created_at', '')
        )
    elif sort_option == "이름순":
        filtered_videos = sorted(
            filtered_videos,
            key=lambda x: x.get('name', '')
        )
    elif sort_option == "크기순":
        filtered_videos = sorted(
            filtered_videos,
            key=lambda x: x.get('file_size', 0) or 0,
            reverse=True
        )

    st.caption(f"총 {len(filtered_videos)}개 영상")

    # 비디오 카드 렌더링
    for video in filtered_videos:
        render_video_card(video, video_type)


# ============================================
# 메인 앱
# ============================================
render_header()

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")

    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()

    st.markdown("""
    ### 📖 사용법
    
    **백업 영상**
    - 블랙박스에서 자동 저장된 영상 목록
    - 오탐 영상은 신고 가능
    
    **오탐 영상**
    - 오탐으로 신고된 영상 목록
    - AI 학습 데이터로 활용
    
    ---
    
    Made with ❤️ using Streamlit
    """)

# 데이터 로드
backup_videos = fetch_backup_videos()
fp_videos = fetch_fp_videos()

# 통계 표시
render_stats(len(backup_videos), len(fp_videos))

st.divider()

# 탭 인터페이스
tab1, tab2 = st.tabs(["📹 백업 영상", "⚠️ 오탐 영상"])

with tab1:
    st.header("백업 영상 목록")
    st.caption("블랙박스에서 자동 저장된 영상입니다. 오탐 영상은 신고해주세요.")
    render_video_grid(backup_videos, "backup")

with tab2:
    st.header("오탐 영상 목록")
    st.caption("오탐으로 신고된 영상입니다. AI 모델 개선에 활용됩니다.")
    render_video_grid(fp_videos, "fp")