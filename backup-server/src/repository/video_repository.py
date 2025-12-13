from sqlalchemy.orm import Session

from src.db.models.video import Video

class VideoRepository:
    def __init__(self, db: Session):
        self.db = db
    def find_by_id(self, id):
        video = self.db.query(Video).filter(Video.id == id).first()
        return video
    def get_backup_video_list(self):
        videos = self.db.query(Video).filter(Video.name.like('[Backup]%')).order_by(Video.created_at.desc()).all()
        return videos
    def get_fp_video_list(self):
        videos = self.db.query(Video).filter(Video.name).like('[FP]%').order_by(Video.created_at.desc()).all()