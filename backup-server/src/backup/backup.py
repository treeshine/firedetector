from multiprocessing import Queue, current_process
from queue import Empty
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import cv2
import pytz
import numpy as np
import os

from src.core.logger import new_logger
from src.core.config import settings
from src.db.models.video import Video

timezone = pytz.timezone(settings.tz)
video_workdir = os.path.join(settings.data_path, "videos")
thumbnail_workdir = os.path.join(settings.data_path, "thumbs")

def video_worker(queue: Queue):
    """
    Queue로부터 이미지들을 consume하여 비디오 생성
    30초단위로 영상을 끊어서 저장
    영상 저장 파일명: backup-<RFC3339 timestamp>.mp4
    """
    # --- logger 설정 ---
    logger = new_logger("worker")

    # --- DB 엔진 설정
    # 별도 워커 프로세스이기에, engine을 새로 초기화 필요
    engine = create_engine(f'sqlite:///{settings.data_path}/video_metadata.db')
    SessionLocal = sessionmaker(bind=engine)
    logger.info(f"가동 시작, PID: {current_process().pid}")
    
    try:
        while True:
            # 첫 프레임여부 및 시작 시간 초기화
            # 시간 시간은 None으로 하는 이유는, 실제 첫 프레임 수신 시에 start_time을 재설저아혀 더 정확한 start_time을 맞출 수 있도록 하기위함
            first = True
            start_time = None
            while True:
                try:
                    # 큐에서 프레임 이미지를 수신. 0.1초 타임아웃을 넣어 무기한 대기 방지.
                    raw = queue.get(timeout=0.1)
                except Empty:
                    # 타임아웃나고 큐가 비어있다면
                    # 만약 30초 청크가 지나면, 그만두기
                    if start_time is not None and datetime.now(timezone) >= start_time + timedelta(seconds=30):
                        break
                    # 이외는 무시하고 다시 기다려보기..
                    continue
            
                # None을 큐로부터 받으면, 종료(main.py 참고)
                if raw is None:
                    logger.info("종료 신호 수신")
                    return

                # 바이트 이미지 디코딩..
                img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    logger.error("이미지 디코딩 실패")
                    continue
            
                # 첫 프레임일 경우, 시간 초기화 및 videoWriter 초기화.
                if first:
                    start_time = datetime.now(timezone)
                    pure_name = f"{start_time.isoformat()}" # RFC3339 Format
                    video_name = os.path.join(video_workdir, f"backup-{pure_name}.mp4")
                    height, width, _ = img.shape
                    video = cv2.VideoWriter(
                        video_name,
                        cv2.VideoWriter_fourcc(*"mp4v"),
                        30,
                        (width, height)
                    )
                    first = False

                # 시간 지나면, 영상 끊음
                if datetime.now(timezone) >= start_time + timedelta(seconds=settings.max_video_len):
                    break

                # 비디오에 프레임 추가
                video.write(img)

            # 영상 파일 Flush
            if video is not None:
                # 비디오 저장
                video.release()
                logger.info(f"비디오 저장: {video_name}")
                thumbnail_name = os.path.join(thumbnail_workdir, f"thumb-{pure_name}.jpeg")
                # 마지막 프레임을 썸네일로...
                cv2.imwrite(thumbnail_name, img)
                logger.info(f"비디오 썸네일 저장: {thumbnail_name}")
                # 영상 메타데이터 DB에 저장
                with SessionLocal() as s:
                    new_video = Video(
                        name = "[Backup] " + pure_name,
                        thumbnail_link = thumbnail_name,
                        video_link = video_name,
                        # file_size = 
                        # duration = 
                    )
                    # 데이터 추가
                    s.add(new_video)
                    # commit
                    s.commit()
                video = None # 혹시모를 중복 release()방지

    # SIGINT 조용히 받기(stacktrace 출력 방지)
    except KeyboardInterrupt:
        pass

    # 워커 종료 전, 혹시라도 저장못한 영상이 있다면 저장.
    finally:
        try:
            if video is not None:
                # 비디오 저장..
                video.release()
                logger.info(f"비디오 저장: {video_name}")
                thumbnail_name = os.path.join(thumbnail_workdir, f"thumb-{pure_name}.jpeg")
                # 마지막 프레임을 썸네일로..
                cv2.imwrite(thumbnail_name, img)
                logger.info(f"비디오 썸네일 저장: {thumbnail_name}")
                # 영상 메타데이터 DB에 저장
                with SessionLocal() as s:
                    new_video = Video(
                        name = "[Backup]" + pure_name,
                        thumbnail_link = thumbnail_name,
                        video_link = video_name,
                        # file_size = 
                        # duration = 
                    )
                    # 데이터 추가
                    s.add(new_video)
                    # commit
                    s.commit()
                video = None # 혹시모를 중복 release()방지
        except Exception:
            logger.warning("아무 video도 저장한 적 없음..")
        finally:
            logger.info("종료..")