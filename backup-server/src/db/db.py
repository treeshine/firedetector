from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.core.config import settings

# 데이터베이스 연결
engine = create_engine(f'sqlite:///{settings.data_path}/video_metadata.db')
# 세션 생성
Session = sessionmaker(bind=engine)
# ORM 기본 클래스 생성
Base = declarative_base()
# 테이블 미존재시 생성
Base.metadata.create_all(bind=engine)