from sqlalchemy.orm import Session

from src.db.models.video import Video


class VideoRepository:
    """
    videos 테이블에 대한 데이터베이스 액세스 영역
    """

    def __init__(self, db: Session):
        self.db = db

    def find_by_id(self, id):
        video = self.db.query(Video).filter(Video.id == id).first()
        return video

    def get_backup_video_list(self):
        videos = (
            self.db.query(Video)
            .filter(Video.type == "BACKUP")
            .order_by(Video.created_at.desc())
            .all()
        )
        return videos

    def get_fp_video_list(self):
        videos = (
            self.db.query(Video)
            .filter(Video.type == "FP")
            .order_by(Video.created_at.desc())
            .all()
        )
        return videos

    def transfer_type_to_fp(self, id):
        video = self.db.query(Video).filter(Video.id == id).first()
        pure_name = video.name[9:]  # [Backup] Prefix 제거
        old_video_key = video.file_path
        old_thumb_key = video.thumbnail_path
        new_video_key = f"videos/fp-backup-{pure_name}.mp4"  # 새로운 video key 생성
        new_thumb_key = f"thumbs/fp-thumb-{pure_name}.jpeg"  # 새로운 thumbnail key 생성
        video.type = "FP"
        video.name = f"[FP] + {pure_name}"
        video.file_path = new_video_key
        video.thumbnail_path = new_thumb_key
        self.db.commit()
        return old_video_key, old_thumb_key, new_video_key, new_thumb_key
