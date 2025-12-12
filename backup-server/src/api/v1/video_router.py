import logging

from multiprocessing import Queue
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.core.config import settings

logger = logging.getLogger("app")
logger.setLevel(settings.log_level)

router = APIRouter(prefix="/ws", tags=["stream"])

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """
    websocket_endpoint - WebSocket으로 이미지를 스트리밍받아서, 저장
    References: https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    """
    await websocket.accept() 
    queue: Queue = websocket.app.state.video_queue
    client_con_info = f"{websocket.client.host}:{websocket.client.port}"
    logger.info(f"Websocket 연결: {client_con_info}")
    try:
        while True:
            # 이미지를 바이트로 수신
            data = await websocket.receive_bytes()
            # 이미지를 Consumer에게 전달
            queue.put(data)
    except WebSocketDisconnect:
        logger.info(f"클라이언트 연결 종료: {client_con_info}")
    except Exception as e:
        logger.error(f"Websocket 에러: {e}")
    finally:
        # 종료 시도
        try:
            await websocket.close()
        except RuntimeError:
            # 이미 닫혀있는 경우, 무시
            pass
