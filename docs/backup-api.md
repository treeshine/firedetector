# API 명세서

## 기본 정보

| 항목 | 내용 |
|------|------|
| Base URL | `/api/v1` |
| WebSocket URL | `/ws/v1` |

---

## WebSocket API

### 비디오 스트리밍

| 항목 | 내용 |
|------|------|
| Endpoint | `WS /ws/v1` |
| 설명 | 이미지를 바이트 스트림으로 수신하여 처리 |
| 데이터 형식 | Binary (bytes) |

---

## REST API

### 백업 비디오

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/videos/backup` | 백업 비디오 목록 조회 |
| GET | `/videos/backup/{id}` | 백업 비디오 파일 조회 |
| GET | `/thumbnail/backup/{id}` | 백업 비디오 썸네일 조회 |

### 오탐(FP) 비디오

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/videos/fp` | 오탐 비디오 목록 조회 |
| GET | `/videos/fp/{id}` | 오탐 비디오 파일 조회 |
| GET | `/thumbnail/fp/{id}` | 오탐 비디오 썸네일 조회 |
| POST | `/fpreport/{id}` | 오탐 신고 (백업 → 오탐 저장소 이동) |

---

## 응답 형식

### 파일 응답
- R2 활성화 시: `RedirectResponse` (클라우드 URL로 리다이렉트)
- R2 비활성화 시: `FileResponse` (로컬 파일 직접 반환)

### 미디어 타입
| 타입 | Content-Type |
|------|--------------|
| 썸네일 | `image/jpeg` |
| 비디오 | `video/mp4` |

---

## 데이터 모델

### Video

| 필드 | 타입 | 설명 |
|------|------|------|
| id | Integer | PK |
| name | String | 영상 이름 |
| thumbnail_path | String | 썸네일 경로 |
| file_path | String | 파일 경로 |
| file_size | Integer | 파일 크기 |
| type | String | 유형 (기본값: `BACKUP`) |
| duration | String | 영상 길이 |
| created_at | DateTime | 생성 시간 |