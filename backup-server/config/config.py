from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    data_path: str # 데이터 저장 루트경로
    # .env파일 매핑하도록 설정
    # 우선순위: 시스템 환경변수 > .env이므로 유의
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )
    
# Setting 인스턴스 생성
settings = Settings()