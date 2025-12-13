from sqlalchemy import Column, Integer, String, DateTime, func

from src.db.db import Base

class Video(Base):
    """
    Video 데이터 모델
    id: PK
    name: 영상이름(타임스탬프 예정)
    이외에 썸네일 링크, 비디오 링크, 파일크기, 영상 길이, 생성시간 등...
    """
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    thumbnail_path = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    duration = Column(String)
    created_at = Column(DateTime(), default = func.now())