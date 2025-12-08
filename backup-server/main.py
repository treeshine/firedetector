from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.config.config import settings
import src.api.v1.video_router as video_router

# FastAPI 인스턴스 생성

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션 생명주기 관리
    Reference: https://fastapi.tiangolo.com/advanced/events/#lifespan
    """
    # --- Startup ---
    print("서버 가동 시작..")
    # TODO: 큐와 워커 프로세스 생성

    yield # (API 핸들링 부분)

    # --- Graceful Shutdown ---
    # TODO: 워커 안전하게 종료할때까지 대기..
    print("서버 닫음...")


# 생명주기 핸들링
app = FastAPI(lifespan=lifespan)

# 요청 라우터 붙이기
app.include_router(video_router.router)