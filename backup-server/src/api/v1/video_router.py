from multiprocessing import Queue
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/ws", tags=["stream"])

@router.websocket("")
async def websocket_endpoint(websocket: WebSocket):
    """
    websocket_endpoint - WebSocket으로 이미지를 스트리밍받아서, 저장
    References: https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    """
    await websocket.accept() 
    queue: Queue = websocket.app.state.video_queue
    try:
        while True:
            # 이미지를 바이트로 수신
            data = await websocket.receive_bytes()
            # TODO: 이미지를 Consumer에게 전달
            print("Image received.")
            queue.put(data)
    except WebSocketDisconnect:
        print("클라이언트 연결 종료")
    except Exception as e:
        print(f"websocket error: {e}")
    finally:
        # 종료 시도
        try:
            await websocket.close()
        except RuntimeError:
            # 이미 닫혀있는 경우, 무시
            pass
