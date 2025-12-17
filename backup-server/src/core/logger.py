import atexit
import json
import logging

from src.core.config import settings


class JsonFormatter(logging.Formatter):
    """
    커스텀 JSON 포매터 생성
    레벨, 메시지, 시간, 코드 모듈 및 라인 등의 정보 제공.
    """

    def format(self, record):
        json_record = {
            "level": record.levelname,
            "message": f"[{record.name.upper()}] {record.getMessage()}",
            "time": self.formatTime(record, "%Y-%m-%d %H:%M:%S"),
            "module": record.module,
            "line": record.lineno,
        }

        # 예외처리 stacktrace제공
        if record.exc_info:
            json_record["exception"] = self.formatException(record.exc_info)

        # 한글로그도 관용
        return json.dumps(json_record, ensure_ascii=False)


def new_logger(name):
    """
    logger 생성
    logger 이름을 받아서 커스텀 logger 생성
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    # JsonFormatter를 handler의 포매터로
    handler.setFormatter(JsonFormatter())
    # handler 등록
    logger.handlers = [handler]
    # 로그 최소 레벨 설정
    logger.setLevel(settings.log_level)

    atexit.register(logging.shutdown)

    return logger


def clear_uvicorn_logger():
    """
    uvicorn 기본 로깅 제거
    """
    logging.getLogger("uvicorn.access").disabled = True
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").disabled = True
    logging.getLogger("uvicorn.error").propagate = False

