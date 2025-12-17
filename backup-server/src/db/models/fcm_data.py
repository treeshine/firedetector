from sqlalchemy import Column, DateTime, Integer, String, func
from src.db.db import Base


class FCMData(Base):
    """
    모바일 토큰 저장
    id: PK
    token: 토큰값
    created_at: 생성시간 등...
    """

    __tablename__ = "fcm_datas"
    id = Column(Integer, primary_key=True)
    token = Column(String)
    created_at = Column(DateTime(), default=func.now())
