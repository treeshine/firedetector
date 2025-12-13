import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse

from src.api.v1.deps import get_video_service
from src.services.video_service import VideoService
from src.core.config import settings

logger = logging.getLogger("app")
logger.setLevel(settings.log_level)

router = APIRouter(prefix="/api/v1", tags=["stream"])

@router.get("/videos/backup")
def get_backup_videos(video_service: VideoService = Depends(get_video_service)):
    return video_service.get_backup_video_list()

@router.get("/thumbnail/backup/{id}")
def read_thumbnail(id, video_service: VideoService = Depends(get_video_service)):
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
def read_video(id, video_service: VideoService = Depends(get_video_service)):
    try:
        res = video_service.get_backup_video_path(id)
        if settings.enable_r2:
            return RedirectResponse(
                url=res
            )
        else:
            return FileResponse(
                path=res,
                media_type="video/mp4",
            )
    except Exception as e:
        logger.error(f"File fetch error {e}")

@router.get("/videos/fp")
def get_fp_videos(video_service: VideoService = Depends(get_video_service)):
    return video_service.get_fp_video_list()