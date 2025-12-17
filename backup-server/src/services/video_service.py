import logging
import os

import boto3

from src.core.config import settings

logger = logging.getLogger("app")
logger.setLevel(settings.log_level)

# R2 API 세팅 - R2는 AWS S3와 같은 sdk이용
if settings.enable_r2:
    s3 = boto3.client(
        "s3",
        endpoint_url=f"https://{settings.cf_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.cf_access_key_id,
        aws_secret_access_key=settings.cf_secret_access_key,
        region_name="auto",  # AWS SDK에서는 필수지만, R2에서는 쓰지않음
    )


class VideoService:
    """
    VideoService - 주요 비즈니스 로직 레이어
    """

    def __init__(self, video_repo):
        self.video_repo = video_repo

    def get_backup_video_list(self):
        return self.video_repo.get_backup_video_list()

    def get_backup_thumbnail(self, id):
        """
        썸네일 데이터 불러오기
        Presigned URL: https://developers.cloudflare.com/r2/api/s3/presigned-urls/
        """
        vid = self.video_repo.find_by_id(id)
        if settings.enable_r2:
            try:
                get_url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": settings.r2_blackbox_bucket_name,
                        "Key": vid.thumbnail_path,
                    },
                    ExpiresIn=600,  # Vaild for 10 minutes
                )
                print(get_url)
                return get_url
            except Exception as e:
                raise e
        else:
            full_path = os.path.join(settings.data_path, vid.thumbnail_path)
            return full_path

    def get_backup_video_path(self, id):
        """
        백업 영상 가져오기
        """
        vid = self.video_repo.find_by_id(id)
        if settings.enable_r2:
            try:
                get_url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": settings.r2_blackbox_bucket_name,
                        "Key": vid.file_path,
                        "ResponseContentType": "video/mp4",
                        "ResponseContentDisposition": "inline",
                    },
                    ExpiresIn=600,  # Vaild for 10 minutes
                )
                logger.info(f"Presigned URL 생성: {get_url}")
                return get_url
            except Exception as e:
                raise e
        else:
            full_path = os.path.join(settings.data_path, vid.file_path)
            return full_path

    def get_fp_video_list(self):
        return self.video_repo.get_fp_video_list()

    def get_fp_thumbnail(self, id):
        """
        썸네일 데이터 불러오기
        Presigned URL: https://developers.cloudflare.com/r2/api/s3/presigned-urls/
        """
        vid = self.video_repo.find_by_id(id)
        if settings.enable_r2:
            try:
                get_url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": settings.r2_fp_bucket_name,
                        "Key": vid.thumbnail_path,
                    },
                    ExpiresIn=600,  # Vaild for 10 minutes
                )
                print(get_url)
                return get_url
            except Exception as e:
                raise e
        else:
            full_path = os.path.join(settings.data_path, vid.thumbnail_path)
            return full_path

    def get_fp_video_path(self, id):
        """
        백업 영상 가져오기
        """
        vid = self.video_repo.find_by_id(id)
        if settings.enable_r2:
            try:
                get_url = s3.generate_presigned_url(
                    "get_object",
                    Params={
                        "Bucket": settings.r2_fp_bucket_name,
                        "Key": vid.file_path,
                        "ResponseContentType": "video/mp4",
                        "ResponseContentDisposition": "inline",
                    },
                    ExpiresIn=600,  # Vaild for 10 minutes
                )
                logger.info(f"Presigned URL 생성: {get_url}")
                return get_url
            except Exception as e:
                raise e
        else:
            full_path = os.path.join(settings.data_path, vid.file_path)
            return full_path

    def single_fp_report(self, id):
        """
        오탐데이터 피드백(블랙박스 백업 -> 오탐 버킷 저장소로 이동)
        """
        (
            old_video_key,
            old_thumb_key,
            new_video_key,
            new_thumb_key,
        ) = self.video_repo.transfer_type_to_fp(id)
        video_path = os.path.join(settings.data_path, new_video_key)
        thumbnail_path = os.path.join(settings.data_path, new_video_key)
        os.rename(os.path.join(settings.data_path, old_video_key), video_path)
        os.rename(os.path.join(settings.data_path, old_thumb_key), thumbnail_path)
        logger.info(f"비디오 파일명 이름 변경 완료: {old_video_key} -> {new_video_key}")
        logger.info(f"썸네일 파일명 이름 변경 완료: {old_thumb_key} -> {new_thumb_key}")
        if settings.enable_r2:
            try:
                # 동영상 버킷 이동
                with open(video_path, "rb") as f:
                    s3.put_object(
                        Bucket=settings.r2_fp_bucket_name,
                        Body=f,
                        ContentType="video/mp4",
                        Key=new_video_key,
                    )
                s3.delete_object(
                    Bucket=settings.r2_fp_bucket_name,
                    Key=new_video_key,
                )
                logger.info(f"버킷 이동 완료: {old_video_key} -> {new_video_key}")

                # 썸네일 이동
                with open(thumbnail_path, "rb") as f:
                    s3.put_object(
                        Bucket=settings.r2_fp_bucket_name,
                        Body=f,
                        Key=new_thumb_key,
                        ContentType="image/jpeg",
                    )
                s3.delete_object(
                    Bucket=settings.r2_fp_bucket_name,
                    Key=new_thumb_key,
                )
                logger.info(f"버킷 이동 완료: {old_thumb_key} -> {new_thumb_key}")
            except Exception as e:
                raise e

