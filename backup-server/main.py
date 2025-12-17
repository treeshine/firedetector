import shutil
from contextlib import asynccontextmanager
from multiprocessing import Process, Queue, current_process

import firebase_admin
import src.api.v1.api_router as api_router
import src.api.v1.ws_router as ws_router
from fastapi import FastAPI
from firebase_admin import credentials
from sqlalchemy.orm import sessionmaker
from src.backup.backup import video_worker
from src.core.config import settings
from src.core.logger import clear_uvicorn_logger, new_logger
from src.db.db import Base, get_engine
from src.middleware.log_httpreq import JsonLogMiddleware


# FastAPI 인스턴스 생성
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 애플리케이션 생명주기 관리
    Reference:
        - https://fastapi.tiangolo.com/advanced/events/#lifespan
        - https://docs.python.org/ko/3/library/multiprocessing.html#multiprocessing-programming
        - https://www.starlette.dev/applications/#storing-state-on-the-app-instance
    """
    # --- Startup ---
    # logger 생성
    clear_uvicorn_logger()
    logger = new_logger("app")
    logger.info(f"서버 가동 시작, PID: {current_process().pid}")

    # Firebase 초기화 추가
    cred = credentials.Certificate("./serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
    logger.info("Firebase 초기화 완료")

    # DB 연결...
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    app.state.engine = engine
    app.state.session_factory = session_factory

    # R2 백업 스토리지 정보 확인
    if settings.enable_r2:
        logger.info(f"백업데이터 R2 저장 활성화. 활성 사용자 ID: {settings.cf_account_id}")
    else:
        logger.info("R2저장 비활성화.")

    # FFmpeg 조회
    if shutil.which("ffmpeg"):
        logger.info("ffmpeg 설치 확인.")
    else:
        logger.warning("ffmpeg 미설치. 브라우저에서 영상 미리보기가 안될 수 있습니다.")

    Base.metadata.create_all(bind=engine)

    # 큐와 워커 프로세스 생성
    queue = Queue()
    worker = Process(target=video_worker, args=(queue,))
    worker.start()

    # queue를 FastAPI 애플리케이션에서 참조할 수 있도록 state에 저장
    app.state.video_queue = queue

    yield  # (FastAPI App 실행)

    # --- Graceful Shutdown ---
    # 워커 및 큐 안전하게 종료할때까지 대기..
    queue.put(None)
    worker.join()
    queue.close()
    queue.cancel_join_thread()
    logger.info("서버 닫음...")


# 생명주기 핸들링 Attach
app = FastAPI(lifespan=lifespan)
app.add_middleware(JsonLogMiddleware)

# 요청 라우터 붙이기
app.include_router(ws_router.router)
app.include_router(api_router.router)


@app.get("/")
async def hellowordl():
    return {"response:" "hello world!"}
