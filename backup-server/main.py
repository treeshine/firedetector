from contextlib import asynccontextmanager
from fastapi import FastAPI
from multiprocessing import Process, Queue

from src.config.config import settings
from src.backup.backup import video_worker
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
    print("서버 가동 시작..")
    # 큐와 워커 프로세스 생성
    queue = Queue()
    worker = Process(target=video_worker, args=(queue, ))
    worker.start()

    # queue를 FastAPI 애플리케이션에서 참조할 수 있도록 state에 저장
    app.state.video_queue = queue

    yield # (FastAPI App 실행)

    # --- Graceful Shutdown ---
    # 워커 안전하게 종료할때까지 대기..
    queue.put(None)
    worker.join()
    queue.close()
    print("서버 닫음...")
    exit(0)


# 생명주기 핸들링 Attach
app = FastAPI(lifespan=lifespan)

# 요청 라우터 붙이기
app.include_router(video_router.router)