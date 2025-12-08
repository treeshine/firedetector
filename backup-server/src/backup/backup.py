from multiprocessing import Queue, current_process
import cv2
import numpy as np

from src.config.config import settings

def video_worker(queue: Queue):
    """
    Queue로부터 이미지들을 consume하여 비디오 생성
    
    TODO: 30초단위로 끊어서 datapath에 저장
    """
    print(f"[Worker] 가동 시작, PID:{current_process().pid}")
    
    workdir = settings.data_path + "/video"
    video_name = "test.mp4"
    first = True
    while True:
        try:
            raw = queue.get()
            
            if raw is None:
                print(f"[Worker] 종료 신호 수신")
                break
            
            img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                print("[Worker] 이미지 디코딩 실패")
                continue
        
            if first:
                height, width, layer = img.shape
                video = cv2.VideoWriter(
                    video_name,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    30,
                    (width, height)
                )
                first = False
            print("프레임 수신 완료!")
            video.write(img)
        except KeyboardInterrupt:
            # SIGINT를 받더라도, 무시. 대신 None을 큐로부터 입력받으면 종료되도록
            pass
        finally:
            if video is not None:
                video.release()