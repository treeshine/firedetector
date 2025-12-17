import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import except_
from src.api.v1.deps import get_fcm_service, get_video_service
from src.core.config import settings
from src.schemas.fcm import TokenRequest
from src.services.fcm_service import FCMService
from src.services.video_service import VideoService

##################################
# Video 메타데이터 REST API 영역 #
# + FCM 로직 영역                #
##################################

logger = logging.getLogger("app")
logger.setLevel(settings.log_level)

router = APIRouter(prefix="/api/v1", tags=["stream"])


@router.get("/videos/backup")
def get_backup_videos(video_service: VideoService = Depends(get_video_service)):
    return video_service.get_backup_video_list()


@router.get("/thumbnail/backup/{id}")
def read_backup_thumbnail(id, video_service: VideoService = Depends(get_video_service)):
    """
    썸네일 이미지 불러오기
    """
    # 클라우드 저장소 우선 이용
    try:
        res = video_service.get_backup_thumbnail(id)
        if settings.enable_r2:
            return RedirectResponse(url=res)
        else:
            return FileResponse(
                path=res,
                media_type="image/jpeg",
            )
    except Exception as e:
        logger.error(f"File fetch error {e}")


@router.get("/videos/backup/{id}")
def read_backup_video(id, video_service: VideoService = Depends(get_video_service)):
    """
    백업 비디오 불러오기
    """
    try:
        res = video_service.get_backup_video_path(id)
        if settings.enable_r2:
            return RedirectResponse(url=res)
        else:
            return FileResponse(
                path=res,
                media_type="video/mp4",
            )
    except Exception as e:
        logger.error(f"File fetch error {e}")


@router.get("/videos/fp")
def get_fp_videos(video_service: VideoService = Depends(get_video_service)):
    """
    오탐 영상목록 불러오기
    """
    return video_service.get_fp_video_list()


@router.get("/thumbnail/fp/{id}")
def read_fp_thumbnail(id, video_service: VideoService = Depends(get_video_service)):
    """
    오탐 썸네일 불러오기
    """
    try:
        res = video_service.get_fp_thumbnail(id)
        if settings.enable_r2:
            return RedirectResponse(url=res)
        else:
            return FileResponse(
                path=res,
                media_type="image/jpeg",
            )
    except Exception as e:
        logger.error(f"File fetch error {e}")


@router.get("/videos/fp/{id}")
def read_fp_video(id, video_service: VideoService = Depends(get_video_service)):
    """
    오탐 영상데이터 불러오기
    """
    try:
        res = video_service.get_fp_video_path(id)
        if settings.enable_r2:
            return RedirectResponse(url=res)
        else:
            return FileResponse(
                path=res,
                media_type="video/mp4",
            )
    except Exception as e:
        logger.error(f"파일을 불러오는 중 에러 발생: {e}")
        raise e


@router.post("/fpreport/{id}")
def fp_report(id, video_service: VideoService = Depends(get_video_service)):
    """
    오탐 데이터 신고(해당 id 블랙박스 아카이브 -> 오탐 저장소로 이동)
    """
    try:
        video_service.single_fp_report(id)
        return Response(status_code=204)
    except Exception as e:
        logger.error(f"에러 발생: {e}")
        raise e


@router.post("/register-token")
def register_token(
    req: TokenRequest, fcm_service: FCMService = Depends(get_fcm_service)
):
    """
    FCM토큰 등록
    """
    try:
        fcm_service.register_client(req.token)
        return Response(status_code=201)
    except Exception as e:
        logger.error(f"FCM토큰 저장 중 에러 발생: {e}")


@router.post("/notify")
def notify_client(fcm_service: FCMService = Depends(get_fcm_service)):
    """
    FCM 알림 전송
    """
    try:
        fcm_service.notify_client()
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"FCM알림 호출 중 에러 발생: {e}")
