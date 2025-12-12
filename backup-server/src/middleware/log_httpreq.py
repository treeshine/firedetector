import time
import json
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.config import settings


logger = logging.getLogger("app")
logger.setLevel(settings.log_level)

class JsonLogMiddleware(BaseHTTPMiddleware):
    """
    JSON 로깅 미들웨어.
    http 요청-응답 체인의 중간에 끼어서 로그를 남기도록 함.
    기존 uvicorn 로깅을 대체.
    """
    async def dispatch(self, request: Request, call_next):
        # 실행시간 측정
        start_time = time.time()
        ## 이후 사이클 거치고, 다시 현재 미들웨어로 돌아오도록 기다림
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # 로그에 남길 데이터
        log_dict = {
            "url": str(request.url),
            "method": request.method,
            "status_code": response.status_code,
            "client_ip": request.client.host,
            "실행시간": f"{process_time:.4f}s",
        }
        
        logger.info(json.dumps(log_dict))
        
        # 응답 계속..
        return response
    