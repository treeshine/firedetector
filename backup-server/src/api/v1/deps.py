from fastapi import Depends

from src.db.db import get_db
from src.repository.video_repository import VideoRepository
from src.services.video_service import VideoService

def get_video_repository(db=Depends(get_db)):
    return VideoRepository(db)

def get_video_service(video_repo: VideoRepository = Depends(get_video_repository)):
    return VideoService(video_repo)