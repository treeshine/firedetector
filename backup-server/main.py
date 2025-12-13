from contextlib import asynccontextmanager
from fastapi import FastAPI
from multiprocessing import Process, Queue, current_process
from sqlalchemy.orm import sessionmaker

from src.core.config import settings
from src.core.logger import new_logger, clear_uvicorn_logger
from src.backup.backup import video_worker
from src.middleware.log_httpreq import JsonLogMiddleware
from src.db.db import Base, get_engine
import src.api.v1.backup_router as backup_router
import src.api.v1.video_router as video_router

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

    # DB 연결...
    engine = get_engine()
    session_factory = sessionmaker(bind=engine)
    app.state.engine = engine
    app.state.session_factory = session_factory
    
    # R2 백업 스토리지 정보 확인
    if settings.enable_r2:
        logger.info(f"백업데이터 R2 저장 활성화. 활성 사용자 ID: {settings.cf_account_id}")
    
    
    Base.metadata.create_all(bind=engine)

    # 큐와 워커 프로세스 생성
    queue = Queue()
    worker = Process(target=video_worker, args=(queue, ))
    worker.start()

    # queue를 FastAPI 애플리케이션에서 참조할 수 있도록 state에 저장
    app.state.video_queue = queue

    yield # (FastAPI App 실행)

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
app.include_router(backup_router.router)
app.include_router(video_router.router)

@app.get("/")
async def hellowordl():
    return { "response:" "hello world!"}