import logging

from firebase_admin import messaging
from src.core.config import settings

logger = logging.getLogger("app")
logger.setLevel(settings.log_level)


class FCMService:
    """
    FCMService - 주요 FCM 비즈니스 로직 레이어
    """

    def __init__(self, fcm_repo):
        self.fcm_repo = fcm_repo

    def register_client(self, token):
        try:
            return self.fcm_repo.register(token)
        except Exception as e:
            raise e

    def notify_client(self):
        fcm_datas = self.fcm_repo.getall()
        for fcm_data in fcm_datas:
            try:  # ✅ for문 안으로 이동
                message = messaging.Message(
                    notification=messaging.Notification(
                        title="화재 감지 발생!", body="화재가 감지되었습니다."
                    ),
                    token=fcm_data.token,
                )
                response = messaging.send(message)
                logger.info(f"response from FCM: {response}")
            except Exception as e:
                logger.warning(f"푸시 알림 보내기 실패 (token: {fcm_data.token}): {e}")
                continue  # 실패해도 다음 토큰으로 계속 진행
