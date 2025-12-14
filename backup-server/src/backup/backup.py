from multiprocessing import Queue, current_process
from queue import Empty
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
import cv2
import pytz
import boto3
import numpy as np
import os
import subprocess

from src.db.db import get_engine
from src.core.logger import new_logger
from src.core.config import settings
from src.core.signals import VideoChunkEnd
from src.db.models.video import Video

timezone = pytz.timezone(settings.tz)
workdir = os.path.join(settings.data_path)

# R2 API 세팅
s3 = boto3.client(
    's3',
    endpoint_url=f'https://{settings.cf_account_id}.r2.cloudflarestorage.com',
    aws_access_key_id=settings.cf_access_key_id,
    aws_secret_access_key=settings.cf_secret_access_key,
    region_name='auto'
)

def video_worker(queue: Queue):
    """
    Queue로부터 이미지들을 consume하여 비디오 생성
    """
    logger = new_logger("worker")
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    logger.info(f"가동 시작, PID: {current_process().pid}")
    
    try:
        while True:
            first = True
            start_time = None
            while True:
                try:
                    # 타임아웃 주입하여 중간에 시간 체크
                    raw = queue.get(timeout=0.1) 
                except Empty:
                    # 시간이 초과시, 이번 영상은 종료
                    if start_time is not None and datetime.now(timezone) >= start_time + timedelta(seconds=30):
                        break
                    continue
            
                # SIGINT 핸들링(main.py 참고)
                if raw is None:
                    logger.info("종료 신호 수신")
                    return

                # 비디오 청크 종료 신호 발생
                if isinstance(raw, VideoChunkEnd):
                    logger.info("웹소켓 연결 종료 감지, 즉시 저장")
                    break

                # 이미지를 numpy 배열로 디코딩
                img = cv2.imdecode(np.frombuffer(raw, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    logger.error("이미지 디코딩 실패")
                    continue
            
                # 첫 이미지 발견 시, 타임스탬프 남기기
                if first:
                    start_time = datetime.now(timezone)
                    pure_name = start_time.strftime("%Y%m%d%H%M%S")
                    video_key = f"videos/blackbox-backup-{pure_name}.mp4"
                    
                    # 임시 파일 (AVI)
                    temp_video_path = os.path.join(workdir, f"temp_{pure_name}.avi")
                    final_video_path = os.path.join(workdir, video_key)
                    
                    height, width, _ = img.shape
                    
                    # 임시로 AVI 저장 
                    video = cv2.VideoWriter(
                        temp_video_path,
                        cv2.VideoWriter_fourcc(*"MJPG"),  # Motion JPEG 
                        30,
                        (width, height)
                    )
                    
                    if not video.isOpened():
                        logger.error("VideoWriter 초기화 실패!")
                        continue
                        
                    first = False
                    frame_written = 0

                # 영상 최대길이 초과 시, 중단
                if datetime.now(timezone) >= start_time + timedelta(seconds=settings.max_video_len):
                    break

                # 프레임 추가 및 카운트 증가
                video.write(img)
                frame_written += 1

            # 비디오 저장 및 업로드
            flush_video(
                pure_name, video, final_video_path, temp_video_path, 
                video_key, img, frame_written, SessionLocal, logger
            )
            
    # SIGINT stacktrace 방지
    except KeyboardInterrupt:
        pass
    finally:
        try:
            # 혹시 찍던게 있으면 마저 저장..
            flush_video(
                pure_name, video, final_video_path, temp_video_path,
                video_key, img, frame_written, SessionLocal, logger
            )
        except Exception:
            logger.warning("아무 video도 저장한 적 없음..")
        finally:
            logger.info("종료..")

def convert_to_h264(input_path, output_path, logger):
    """
    ffmpeg로 H.264 변환
    """
    try:
        command = [
            'ffmpeg',
            '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'ultrafast',  # 빠른 인코딩
            '-crf', '23',
            '-movflags', '+faststart',  # 스트리밍 최적화
            '-y',
            output_path
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # 30초 타임아웃
        )
        
        if result.returncode == 0:
            logger.info(f"ffmpeg 변환 성공: {output_path}")
            return True
        else:
            logger.error(f"ffmpeg 변환 실패: {result.stderr}")
            return False
            
    except FileNotFoundError:
        logger.error("ffmpeg가 설치되지 않음!")
        return False
    except subprocess.TimeoutExpired:
        logger.error("ffmpeg 변환 타임아웃")
        return False
    except Exception as e:
        logger.error(f"ffmpeg 에러: {e}")
        return False

def flush_video(pure_name, video, final_video_path, temp_video_path, video_key, img, frame_written, SessionLocal, logger):
    """
    영상 파일 Flush(로컬 저장 + 클라우드 업로드)
    """
    if video is not None:
        logger.info("데이터 저장 시도..")
        duration_seconds = frame_written / 30
        video_time = timedelta(seconds=int(round(duration_seconds)))
        
        # 1. OpenCV 비디오 저장
        video.release()
        logger.info(f"임시 비디오 저장: {temp_video_path}")
        
        # 2. ffmpeg로 H.264 변환
        logger.info("브라우저 호환 형식으로 변환 중...")
        conversion_success = convert_to_h264(temp_video_path, final_video_path, logger)
        
        if conversion_success:
            # 변환 성공 - 임시 파일 삭제
            try:
                os.remove(temp_video_path)
            except:
                pass
            logger.info(f"최종 비디오: {final_video_path}")
        else:
            # 변환 실패 - 임시 파일을 그대로 사용
            logger.warning("ffmpeg 변환 실패, 원본 파일 사용")
            logger.warning("브라우저에서 재생이 안 될 수 있습니다!")
            try:
                os.rename(temp_video_path, final_video_path)
            except:
                logger.error("파일 이동 실패")
                return
        
        # 3. 썸네일 저장
        thumb_key = f"thumbs/blackbox-thumb-{pure_name}.jpeg"
        thumbnail_path = os.path.join(workdir, thumb_key)
        cv2.imwrite(thumbnail_path, img)
        logger.info(f"썸네일 저장: {thumbnail_path}")

        # 4. R2 업로드
        if settings.enable_r2:
            try:
                with open(final_video_path, "rb") as f:
                    s3.put_object(
                        Bucket=settings.r2_blackbox_bucket_name,
                        Body=f,
                        ContentType='video/mp4',
                        Key=video_key,
                    )
                logger.info(f"영상 업로드 완료: {video_key}")
                
                with open(thumbnail_path, "rb") as f:
                    s3.put_object(
                        Bucket=settings.r2_blackbox_bucket_name,
                        Body=f,
                        Key=thumb_key,
                        ContentType='image/jpeg',
                    )
                logger.info(f"썸네일 업로드 완료: {thumb_key}")
            except Exception as e:
                logger.error(f"R2 업로드 실패: {e}")
                return

        # 5. DB 저장
        try:
            with SessionLocal() as s:
                new_video = Video(
                    name = "[Backup] " + pure_name,
                    thumbnail_path = thumb_key,
                    file_path = video_key,
                    file_size = f"{(float(os.path.getsize(final_video_path)) / (1024*1024)):.2f} MB", 
                    duration = str(video_time)
                )
                s.add(new_video)
                s.commit()
            logger.info("DB 저장 완료")
        except Exception as e:
            logger.error(f"DB 저장 실패: {e}")
        video = None