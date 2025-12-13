from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Settings: 환경변수 및 기타 config 불러옴
    References: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#hide-none-type-values
    """
    data_path: str = "/var/fddata" # 데이터 저장 루트경로
    tz: str = "Asia/Seoul" # Timezone
    max_video_len: int = 60 # 기본 영상 청크 길이 60 ~ 90초 권장.
    log_level: str = "INFO" # 최소 출력 로그 레벨. DEBUG, INFO, WARNING, ERROR, CRITICAL
    enable_r2: bool = False # 기본적으로 Cloudflare R2 사용 안함
    cf_account_id: str # Cloudlfare Account ID
    cf_access_key_id: str # Cloudflare Access Key ID
    cf_secret_access_key: str # Cloudflare Secret Access Key 
    r2_blackbox_bucket_name: str # R2 블랙박스 버킷이름
    r2_fp_bucket_name: str # R2 오탐데이터 버킷
    # .env파일 매핑하도록 설정
    # 우선순위: 시스템 환경변수 > .env이므로 유의
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8'
    )
    
# Setting 인스턴스 생성
settings = Settings()