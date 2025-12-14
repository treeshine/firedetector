from fastapi import Request
from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base

from src.core.config import settings

def get_engine() -> Engine:
    """
    데이터베이스 engine 초기화
    """
    engine = create_engine(f'sqlite:///{settings.data_path}/video_metadata.db')
    return engine

def get_db(request: Request):
    """
    DI: 데이터베이스 세션 생성
    Reference: https://fastapi.tiangolo.com/ko/tutorial/dependencies/dependencies-with-yield/
    """
    SessionLocal: sessionmaker = request.app.state.session_factory
    db: Session =  SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ORM 기본 클래스 생성
Base = declarative_base()