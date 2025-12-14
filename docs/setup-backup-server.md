# 백업 서버 세팅 가이드

## 가상환경 생성 및 패키지 설치
Python 3.14 환경에서 가상환경으로 구성하는 가이드를 제공합니다.

```bash
cd backup-server
python3 -m venv .venv
source .venv/bin/activate # 가상환경 활성화

pip install -r requirements.txt
```

이후, 가상환경 비활성화는 아래 명령어를 통해 비활성화가 가능합니다.

```bash
deactivate
```

## 환경변수 설정
`.env.example`을 기반으로 환경변수의 내용을 구성합니다.

```bash
cp .env.example .env
```

파일이 복사되었다면, `.env`의 내용을 입맛에 맞춰 구성합니다.
```bash
DATA_PATH=/var/fddata                            # 데이터 저장 경로(영상 백업 데이터 및 sqlite 저장)
TZ=Asia/Seoul                                    # TimeZone
MAX_VIDEO_LEN=60                                 # 최대 비디오 조각 길이
LOG_LEVEL=INFO                                   # 로그 출력 레벨(DEBUG, INFO, WARNING, ERROR, CRITICAL)
enable_r2=False                                  # R2백업 활성화여부. True시 아래 정보들을 모두 입력하시오.
CF_ACCOUNT_ID=<YOUR_CF_ACCOUNT_ID>               # Cloudflare Account ID
CF_ACCESS_KEY_ID=<YOUR_CF_ACCESS_KEY_ID>         # Cloudflare Access Key ID
CF_SECRET_ACCESS_KEY=<YOUR_CF_SECRET_ACCESS_KEY> # Cloudflare Secret Access Key 
R2_BLACKBOX_BUCKET_NAME=blackbox-bucket          # blackbox 버킷명
R2_FP_BUCKET_NAME=fp-bucket                      # 오탐데이터 버킷명
```

> [!WARNING]
> **`.env`파일은 시스템 환경변수보다 더 낮은 우선순위를 가집니다.**   
> [`src/core/config`에 구성된 기본값] < [`.env`] < [시스템 환경변수] 덮어씌워진다고 이해하시면 됩니다.   
> 참고: [Pydantic Official Document](https://docs.pydantic.dev/latest/concepts/pydantic_settings/#dotenv-env-support)

## FFmpeg 설치
동영상 인코딩을 위해, FFmpeg를 필요로 합니다.    
LGPL 라이선스이며, 서브프로세스로 호출하기에, 별도의 이슈는 없습니다.   
[Download FFmpeg](https://www.ffmpeg.org/download.html)을 참조하십시오.  

## 서버 시작하기
가상환경이 활성화되어있다면, `fastapi` CLI를 사용할 수 있습니다.

```bash
fastapi run main.py
```