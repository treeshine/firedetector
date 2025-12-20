# API 명세서

## 기본 정보

| 항목 | 내용 |
|------|------|
| Base URL | `http://{host}:{port}` |
| API Version | v1 |

---

## 1. WebSocket API

### 1.1 비디오 스트리밍

WebSocket을 통해 실시간으로 이미지/비디오 청크를 전송합니다.

| 항목 | 내용 |
|------|------|
| **Endpoint** | `ws://{host}:{port}/ws/v1` |
| **Protocol** | WebSocket |
| **Data Format** | Binary (bytes) |

**연결 흐름:**
1. 클라이언트가 WebSocket 연결 요청
2. 서버가 연결 수락 (`accept`)
3. 클라이언트가 이미지 데이터를 바이트로 전송
4. 서버가 데이터를 내부 큐에 저장
5. 연결 종료 시 `VideoChunkEnd` 시그널 발생

**이벤트:**

| 이벤트 | 설명 |
|--------|------|
| 연결 성공 | 서버 로그: `Websocket 연결: {host}:{port}` |
| 연결 종료 | 서버 로그: `클라이언트 연결 종료: {host}:{port}` |
| 에러 발생 | 서버 로그: `Websocket 에러: {error}` |

---

## 2. REST API

### 2.1 백업 비디오

#### 2.1.1 백업 비디오 목록 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/videos/backup` |
| **Content-Type** | `application/json` |

**Response:**
```json
[
  {
    "id": 1,
    "name": "1704067200",
    "thumbnail_path": "/thumbnails/1704067200.jpg",
    "file_path": "/videos/1704067200.mp4",
    "file_size": 1048576,
    "type": "BACKUP",
    "duration": "00:01:30",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### 2.1.2 백업 비디오 썸네일 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/thumbnail/backup/{id}` |
| **Response Type** | `image/jpeg` 또는 `RedirectResponse` (R2 활성화 시) |

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | ✓ | 비디오 고유 ID |

**Response:**
- R2 비활성화: 이미지 파일 직접 반환 (`image/jpeg`)
- R2 활성화: 클라우드 저장소 URL로 리다이렉트 (302)

#### 2.1.3 백업 비디오 파일 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/videos/backup/{id}` |
| **Response Type** | `video/mp4` 또는 `RedirectResponse` (R2 활성화 시) |

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | ✓ | 비디오 고유 ID |

**Response:**
- R2 비활성화: 비디오 파일 직접 반환 (`video/mp4`)
- R2 활성화: 클라우드 저장소 URL로 리다이렉트 (302)

---

### 2.2 오탐(False Positive) 비디오

#### 2.2.1 오탐 비디오 목록 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/videos/fp` |
| **Content-Type** | `application/json` |

**Response:**
```json
[
  {
    "id": 1,
    "name": "1704067200",
    "thumbnail_path": "/thumbnails/fp/1704067200.jpg",
    "file_path": "/videos/fp/1704067200.mp4",
    "file_size": 1048576,
    "type": "FP",
    "duration": "00:01:30",
    "created_at": "2024-01-01T00:00:00"
  }
]
```

#### 2.2.2 오탐 비디오 썸네일 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/thumbnail/fp/{id}` |
| **Response Type** | `image/jpeg` 또는 `RedirectResponse` (R2 활성화 시) |

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | ✓ | 비디오 고유 ID |

#### 2.2.3 오탐 비디오 파일 조회

| 항목 | 내용 |
|------|------|
| **Endpoint** | `GET /api/v1/videos/fp/{id}` |
| **Response Type** | `video/mp4` 또는 `RedirectResponse` (R2 활성화 시) |

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | ✓ | 비디오 고유 ID |

#### 2.2.4 오탐 신고

백업 비디오를 오탐으로 신고하여 오탐 저장소로 이동시킵니다.

| 항목 | 내용 |
|------|------|
| **Endpoint** | `POST /api/v1/fpreport/{id}` |
| **Content-Type** | `application/json` |

**Path Parameters:**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | integer | ✓ | 신고할 비디오 ID |

**Response:**

| 상태 코드 | 설명 |
|-----------|------|
| 204 | No Content - 성공 |
| 500 | Internal Server Error |

---

### 2.3 FCM (Firebase Cloud Messaging)

#### 2.3.1 FCM 토큰 등록

모바일 푸시 알림을 위한 FCM 토큰을 등록합니다.

| 항목 | 내용 |
|------|------|
| **Endpoint** | `POST /api/v1/register-token` |
| **Content-Type** | `application/json` |

**Request Body:**
```json
{
  "token": "fcm_token_string"
}
```

**Response:**
```json
{
  "message": "registerd",
  "id": 1
}
```

#### 2.3.2 FCM 알림 전송

등록된 클라이언트에게 푸시 알림을 전송합니다.

| 항목 | 내용 |
|------|------|
| **Endpoint** | `POST /api/v1/notify` |
| **Content-Type** | `application/json` |

**Response:**

| 상태 코드 | 설명 |
|-----------|------|
| 200 | OK - 알림 전송 성공 |
| 500 | Internal Server Error |

---

## 3. API 엔드포인트 요약

| Method | Endpoint | 설명 |
|--------|----------|------|
| WS | `/ws/v1` | 비디오 스트리밍 WebSocket |
| GET | `/api/v1/videos/backup` | 백업 비디오 목록 조회 |
| GET | `/api/v1/thumbnail/backup/{id}` | 백업 비디오 썸네일 조회 |
| GET | `/api/v1/videos/backup/{id}` | 백업 비디오 파일 조회 |
| GET | `/api/v1/videos/fp` | 오탐 비디오 목록 조회 |
| GET | `/api/v1/thumbnail/fp/{id}` | 오탐 비디오 썸네일 조회 |
| GET | `/api/v1/videos/fp/{id}` | 오탐 비디오 파일 조회 |
| POST | `/api/v1/fpreport/{id}` | 오탐 신고 |
| POST | `/api/v1/register-token` | FCM 토큰 등록 |
| POST | `/api/v1/notify` | FCM 알림 전송 |

---

## 4. 데이터 모델

### 4.1 Video

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| id | integer | ✓ | auto | Primary Key |
| name | string | - | - | 영상 이름 (타임스탬프) |
| thumbnail_path | string | - | - | 썸네일 파일 경로 |
| file_path | string | - | - | 비디오 파일 경로 |
| file_size | integer | - | - | 파일 크기 (bytes) |
| type | string | - | "BACKUP" | 비디오 타입 (BACKUP, FP) |
| duration | string | - | - | 영상 길이 |
| created_at | datetime | - | now() | 생성 시간 |

### 4.2 FCMData

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| id | integer | ✓ | auto | Primary Key |
| token | string | - | - | FCM 토큰 값 |
| created_at | datetime | - | now() | 생성 시간 |

---

## 5. 에러 응답

### 5.1 HTTP 에러 코드

| 코드 | 설명 |
|------|------|
| 200 | OK - 요청 성공 |
| 204 | No Content - 성공 (응답 본문 없음) |
| 302 | Redirect - 클라우드 저장소로 리다이렉트 |
| 400 | Bad Request - 잘못된 요청 |
| 404 | Not Found - 리소스를 찾을 수 없음 |
| 500 | Internal Server Error - 서버 내부 오류 |

### 5.2 WebSocket 에러 코드

| 코드 | 설명 |
|------|------|
| 1000 | 정상 종료 |
| 1006 | 비정상 종료 |

---

## 6. 설정 옵션

| 설정 | 설명 |
|------|------|
| `enable_r2` | Cloudflare R2 저장소 사용 여부. `true`인 경우 파일 요청 시 R2 URL로 리다이렉트 |
| `log_level` | 로깅 레벨 설정 |