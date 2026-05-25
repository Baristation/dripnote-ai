# dripnote-ai 프로젝트 리서치 문서

> 최초 작성: 2026-05-25 / 최종 수정: 2026-05-25

---

## 1. 프로젝트 개요

**dripnote-ai**는 커피 추천 플랫폼 **Baristation**의 AI 백엔드 시스템이다. FastAPI 기반으로 구축되어 있으며, LangGraph ReAct Agent, RAG(Retrieval-Augmented Generation), 머신러닝 파이프라인을 결합해 사용자의 커피 관련 질문에 지능적으로 응답하고 제품을 추천한다.

### 핵심 기능

| 기능 | 설명 |
|------|------|
| 커피 Q&A / 제품 추천 | ReAct Agent가 툴을 선택해 Qdrant 검색 + LLM 답변 |
| 사이트 안내 | `search_website_docs` 툴 (메뉴얼 RAG 추가 시 활성화) |
| 제품 인덱싱 | MySQL → OpenAI Embedding → Qdrant 배치 파이프라인 |
| 모델 훈련 | SFT(Supervised Fine-Tuning) 파이프라인 (현재 스텁) |

### 프로덕션 접속 정보

| 용도 | 주소 |
|------|------|
| SSH | `ssh -p 2257 baristation-ai@baristation.iptime.org` |
| Swagger UI | `http://baristation.iptime.org/docs` |
| Health Check | `http://baristation.iptime.org/health` |

---

## 2. 기술 스택

### 핵심 의존성

| 분류 | 기술 |
|------|------|
| API 프레임워크 | FastAPI, Uvicorn |
| LLM 오케스트레이션 | LangChain, LangGraph (`>=1.0.0,<1.1.0`) |
| 에이전트 | LangGraph `create_react_agent` (ReAct 패턴) |
| 벡터 DB | Qdrant |
| 임베딩 | OpenAI `text-embedding-3-small` (1536차원) |
| LLM | OpenAI `gpt-4.1-mini` (설정 가능) |
| 관계형 DB | MySQL (SQLAlchemy + pymysql) |
| 캐시 / 잡 스토리지 | Redis |
| 데이터 검증 | Pydantic v2 |
| 배포 | Docker, Nginx (Blue-Green) |
| CI/CD | GitHub Actions (self-hosted runner) |
| ML (옵셔널) | transformers, PEFT, TRL, sentence-transformers |
| 재시도 | tenacity |

### 개발 도구

- **Python**: >=3.11
- **린터**: ruff (line-length=100, target=py311)
- **테스트**: pytest + httpx

---

## 3. 디렉토리 구조 및 역할

```
dripnote-ai/
├── apps/
│   ├── api/
│   │   ├── main.py          # FastAPI 앱 인스턴스, 라우터 등록, 전역 예외 핸들러
│   │   └── routes/
│   │       ├── chat.py      # POST /api/chat
│   │       ├── rag.py       # POST /api/rag/index/products, GET /api/rag/index/jobs/{id}
│   │       └── training.py  # POST /api/train, GET /api/train/jobs/{id}
│   └── worker/
│       └── main.py          # 워커 플레이스홀더 (미구현)
│
├── src/
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (환경변수 → 설정 객체)
│   │   ├── security.py      # X-Internal-Key 헤더 인증 의존성
│   │   ├── redis.py         # Redis 클라이언트 팩토리 (LRU 캐시)
│   │   └── logging.py       # 로깅 기본 설정
│   │
│   ├── db/
│   │   ├── mysql.py         # SQLAlchemy 엔진 팩토리
│   │   └── repositories/
│   │       └── product_read_repository.py  # 제품/원두/플레이버 읽기 전용 쿼리
│   │
│   ├── llm/
│   │   ├── clients/
│   │   │   └── openai_client.py   # ChatOpenAI, OpenAIEmbeddings 팩토리
│   │   ├── prompts/
│   │   │   └── agent_prompt.py    # ReAct 에이전트 시스템 프롬프트
│   │   └── tools/
│   │       ├── product_search_tool.py  # search_products 툴 (Qdrant + MySQL)
│   │       └── doc_search_tool.py      # search_website_docs 툴 (메뉴얼 RAG 스텁)
│   │
│   ├── graph/
│   │   └── workflows/
│   │       └── agent_graph.py     # AgentGraphWorkflow + 메타데이터 추출
│   │
│   ├── rag/
│   │   ├── documents/
│   │   │   └── product_document.py       # 제품 → 임베딩용 텍스트 / Qdrant 페이로드
│   │   ├── vectorstores/
│   │   │   └── qdrant_store.py           # Qdrant 컬렉션 관리, upsert, 검색
│   │   └── pipelines/
│   │       └── product_index_pipeline.py # 전체 인덱싱 오케스트레이션
│   │
│   ├── ml/
│   │   ├── datasets/
│   │   │   └── jsonl_dataset.py       # JSONL 파일 로더
│   │   ├── preprocessing/
│   │   │   └── format_supervised.py   # SFT 포맷 변환
│   │   ├── trainers/
│   │   │   └── sft_trainer.py         # SFTTrainerService (현재 스텁)
│   │   ├── inference/
│   │   │   └── predictor.py           # LocalPredictor (현재 스텁)
│   │   └── evaluation/
│   │       └── metrics.py             # exact_match 메트릭
│   │
│   └── services/
│       ├── chat_service.py      # AgentGraphWorkflow 위임
│       ├── training_service.py  # 경로 검증 + 훈련 위임
│       ├── job_service.py       # Redis 기반 비동기 잡 상태 추적
│       └── cache_service.py     # Redis JSON 캐시 래퍼
│
├── scripts/
│   ├── train.py               # CLI: 훈련 실행
│   └── index_products.py      # CLI: 제품 인덱싱 실행
│
├── tests/
│   ├── api/                   # 헬스체크, 인증 테스트
│   ├── graph/                 # 에이전트 워크플로우 테스트
│   ├── llm/tools/             # search_products 툴 단위 테스트
│   ├── rag/                   # 문서 생성, 리포지토리 머지 테스트
│   ├── ml/                    # 메트릭 테스트
│   └── services/              # 경로 순회 공격 방어 테스트
│
├── deploy/
│   ├── deploy.sh              # Blue-Green 배포 스크립트
│   └── compose.blue-green.yml # Blue/Green 컨테이너 정의
│
├── nginx/
│   └── nginx.conf             # 역방향 프록시 설정
│
├── data/
│   ├── raw/                   # 원본 데이터셋
│   ├── processed/             # 전처리된 JSONL 데이터
│   └── external/              # 외부 수집 데이터
│
└── models/
    ├── checkpoints/           # 훈련 체크포인트
    ├── exported/              # 프로덕션 모델
    └── tokenizers/            # 토크나이저 파일
```

---

## 4. 아키텍처 상세

### 4.1 전체 요청 흐름

```
POST /api/chat { "message": "..." }
    ↓
FastAPI Route (apps/api/routes/chat.py)
    ↓
ChatService.generate_reply()
    ↓
AgentGraphWorkflow.run()
    ↓
create_react_agent (LangGraph ReAct 루프)
    ↓
LLM이 툴 선택 → search_products / search_website_docs / 직접 답변
    ↓
External Services: OpenAI / Qdrant / MySQL
    ↓
{ answer, recommended_product_ids, sources }
    ↓
HTTP Response
```

### 4.2 ReAct Agent 동작 방식

에이전트는 **Thought → Action → Observation** 루프를 반복하며 답변을 생성한다.

```
질문: "산미 강한 에티오피아 원두 추천해주고 사이트 구매 방법도 알려줘"

[Thought] 제품 추천과 구매 안내 두 가지가 필요하다.
[Action]  search_products("산미 강한 에티오피아 원두")
[Obs]     [PRODUCTS_META]...[/PRODUCTS_META] + 제품 문서 텍스트

[Thought] 구매 방법은 사이트 문서가 필요하다.
[Action]  search_website_docs("구매 방법")
[Obs]     "현재 사이트 이용 안내 검색 기능을 준비 중입니다."

[Final]   두 결과를 합쳐 최종 한국어 답변 생성
```

단일 질문(툴 1회) vs 복합 질문(툴 N회)에 LLM이 자율적으로 대응한다.

### 4.3 툴 설계

| 툴 | 파일 | 동작 | 현황 |
|----|------|------|------|
| `search_products` | `src/llm/tools/product_search_tool.py` | 쿼리 임베딩 → Qdrant 검색 → MySQL 보강 → 결과 직렬화 | 완료 |
| `search_website_docs` | `src/llm/tools/doc_search_tool.py` | 웹사이트 메뉴얼 RAG | 스텁 (메뉴얼 컬렉션 구축 후 구현) |

**툴 응답 포맷** (`search_products` 기준):

```
[PRODUCTS_META]
[{"product_id": 42, "product_name": "예가체프 내추럴", "roaster_name": "블루보틀",
  "matched_flavors": ["자스민", "레몬"], "score": 0.91}]
[/PRODUCTS_META]

Product: 예가체프 내추럴 (Yirgacheffe Natural)
Roaster: 블루보틀 (Blue Bottle)
...
```

`[PRODUCTS_META]` 블록은 `extract_metadata_from_messages()`가 메시지 히스토리에서 파싱해 `recommended_product_ids`, `sources` 필드로 변환한다.

### 4.4 메타데이터 추출 흐름

```python
# agent_graph.py
def extract_metadata_from_messages(messages) -> tuple[list[int], list[dict]]:
    # ToolMessage 객체에서 [PRODUCTS_META]...[/PRODUCTS_META] 블록 파싱
    # 같은 product_id가 여러 번 검색됐을 때 score 높은 것 유지
    # → (product_ids, sources) 반환
```

### 4.5 제품 인덱싱 파이프라인

```
MySQL (제품 + 원두 + 플레이버)
    ↓
build_product_document()   # 다국어(KO+EN) 임베딩용 텍스트 생성
    ↓
OpenAI text-embedding-3-small  # 1536차원 벡터, 배치 처리 + 지수 백오프 재시도
    ↓
Qdrant upsert              # product_id를 point ID로, COSINE 거리 컬렉션
```

---

## 5. 핵심 설계 패턴

### 5.1 지연 초기화 + 스레드 안전 싱글턴

OpenAI 클라이언트, Qdrant 클라이언트, Redis 클라이언트, MySQL 엔진, AgentGraphWorkflow 내부 앱 모두 동일 패턴:

```python
_app = None
_lock = threading.Lock()

def _get_app():
    if _app is None:
        with _lock:
            if _app is None:      # Double-checked locking
                _app = create_react_agent(...)
    return _app
```

### 5.2 서비스 레이어 격리

```
Routes          → 요청/응답 직렬화만 담당
ChatService     → AgentGraphWorkflow 위임
AgentGraphWorkflow → create_react_agent + 메타데이터 추출
Tools           → 외부 시스템(Qdrant, MySQL) 접근 단위
```

### 5.3 N+1 문제 방지

툴 내부에서 플레이버는 제품별 쿼리 대신 `IN` 절 일괄 조회 후 Python 병합:

```python
# product_search_tool.py
products = fetch_products_by_ids(product_ids)        # 단일 쿼리
flavors_by_id = fetch_flavors_by_product_ids(product_ids)  # 단일 쿼리
```

### 5.4 툴 확장 방법

새 지식 소스 추가 시 변경 범위가 최소화된다:

1. `src/llm/tools/` 에 `@tool` 데코레이터 함수 작성
2. `agent_graph.py`의 `tools=[...]` 리스트에 추가
3. `agent_prompt.py`에 툴 사용 판단 기준 예시 추가

### 5.5 보안

| 위협 | 대응 |
|------|------|
| 미인증 내부 API 접근 | `X-Internal-Key` 헤더 검증 (`security.py`) |
| 경로 순회 공격 | `path.resolve().is_relative_to(allowed_dir)` 검사 |
| SQL 인젝션 | SQLAlchemy `bindparam(expanding=True)` 사용 |
| 읽기 전용 DB 접근 | `ai_readonly` MySQL 계정 |

### 5.6 에러 핸들링 전략

```
# main.py 글로벌 핸들러
OpenAI RateLimitError            → 503 Service Unavailable
OpenAI AuthenticationError       → 502 Bad Gateway
OpenAI APIConnectionError        → 503 Service Unavailable
MySQL OperationalError           → 503 Service Unavailable
Qdrant ResponseHandlingException → 503 Service Unavailable
RedisError                       → 503 Service Unavailable
```

---

## 6. API 엔드포인트

### 공개 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| GET | `/health` | 헬스체크 (외부 의존성 없음) |
| POST | `/api/chat` | 커피 Q&A / 제품 추천 |

### 내부 엔드포인트 (X-Internal-Key 필요)

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/rag/index/products` | 제품 벡터 인덱싱 트리거 |
| GET | `/api/rag/index/jobs/{job_id}` | 인덱싱 잡 상태 조회 |
| POST | `/api/train` | 모델 파인튜닝 시작 |
| GET | `/api/train/jobs/{job_id}` | 훈련 잡 상태 조회 |

### Chat API 요청/응답

```json
// Request — use_rag 필드 없음, 에이전트가 자동 판단
{
  "message": "산미가 강한 에티오피아 원두 추천해줘"
}

// Response
{
  "answer": "...",
  "workflow": "agent",
  "recommended_product_ids": [42, 17, 8],
  "sources": [
    {
      "product_id": 42,
      "product_name": "예가체프 내추럴",
      "roaster_name": "블루보틀",
      "matched_flavors": ["자스민", "레몬"],
      "score": 0.91
    }
  ]
}
```

---

## 7. 데이터 모델

### 제품 문서 (임베딩용 텍스트)

`build_product_document()`가 생성하는 다국어 임베딩 텍스트:

```
Product: {ko} ({en})
Roaster: {ko} ({en})
Beans:
- {bean_name_ko} ({bean_name_en}), origin=..., region=..., process=..., variety=..., altitude=...
Roast level: ...
Acidity: ... / Sweetness: ... / Body: ... / Balance: ...
Flavor categories: ...
Flavor notes: ...
Description: ...
Product URL: ...
```

### Qdrant 페이로드 (메타데이터)

```python
{
  "productId": int,
  "beanIds": list[int],
  "productNameKo": str,
  "productNameEn": str,
  "roastLevel": str,
  "flavorCategories": list[str],
  "flavorNotes": list[str],
  "updatedAt": str,
  "document": str,   # 색인에 사용한 원본 텍스트
}
```

### 잡 상태 (Redis)

```python
{
  "job_id": "index-1716800000-a3f2",
  "status": "queued" | "running" | "completed" | "failed",
  "created_at": str,
  "started_at": str | None,
  "finished_at": str | None,
  "error": str | None
}
```

---

## 8. 환경 변수

| 변수 | 예시값 | 설명 |
|------|--------|------|
| `APP_NAME` | dripnote-ai | 앱 이름 |
| `APP_ENV` | development | 실행 환경 |
| `INTERNAL_API_KEY` | secret-key | 내부 API 인증 키 |
| `OPENAI_API_KEY` | sk-... | OpenAI API 키 |
| `OPENAI_MODEL` | gpt-4.1-mini | 사용 LLM 모델 |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | 임베딩 모델 |
| `QDRANT_URL` | http://qdrant:6333 | Qdrant 주소 |
| `QDRANT_API_KEY` | - | Qdrant 인증 키 |
| `QDRANT_COLLECTION` | baristation-products | 컬렉션 이름 |
| `QDRANT_VECTOR_SIZE` | 1536 | 벡터 차원 |
| `QDRANT_TOP_K` | 5 | 검색 결과 수 |
| `REDIS_HOST` | redis | Redis 호스트 |
| `REDIS_PORT` | 6379 | Redis 포트 |
| `REDIS_DB` | 0 | Redis DB 번호 |
| `REDIS_KEY_PREFIX` | dripnote | 캐시 키 접두사 |
| `BACKEND_MYSQL_HOST` | db | MySQL 호스트 |
| `BACKEND_MYSQL_PORT` | 8005 | MySQL 포트 |
| `BACKEND_MYSQL_DATABASE` | baristation | 데이터베이스명 |
| `BACKEND_MYSQL_USER` | ai_readonly | 읽기 전용 계정 |
| `BACKEND_MYSQL_PASSWORD` | - | MySQL 비밀번호 |

---

## 9. 배포 아키텍처

### 프로덕션 컨테이너 현황

```
CONTAINER       IMAGE                   STATUS       PORTS
ai-api-blue     dripnote-ai:latest      Up (healthy) 8000/tcp
nginx           nginx:1.27-alpine       Up           0.0.0.0:80->80/tcp
redis           redis:7-alpine          Up (healthy) 6379/tcp
qdrant          qdrant/qdrant:v1.12.4   Up (healthy) 6333-6334/tcp
```

### 개발 환경 (docker-compose.yml)

```
localhost:8000  →  ai-api (소스 코드 마운트)
localhost:6333  →  qdrant:1.12.4
localhost:6379  →  redis:7-alpine
```

### 프로덕션 (Blue-Green 배포)

```
Internet (port 80)
  ↓
Nginx (nginx.conf)
  ↓  upstream: ai-api-blue:8000 | ai-api-green:8000
ai-api-blue / ai-api-green  (한 번에 하나만 활성)
  ↓
Qdrant + Redis (공유 인프라, docker-compose.prod.yml)
```

### Blue-Green 배포 시나리오 (`deploy.sh`)

1. 현재 실행 중인 컨테이너 확인 (blue or green)
2. 반대 컨테이너 시작
3. 15초 대기 후 `/health` 엔드포인트 폴링 (12회 × 5초)
4. 헬스체크 통과 → `sed`로 nginx 업스트림 교체 → `nginx -s reload`
5. 이전 컨테이너 중지/삭제
6. 헬스체크 실패 → 새 컨테이너 롤백, 종료

### CI/CD (`.github/workflows/deploy.yml`)

- **트리거**: `main` 브랜치 push
- **동시성**: 이전 배포 취소 후 새 배포 시작
- **러너**: self-hosted
- **단계**: checkout → `.env` 생성 (Secrets) → Docker 빌드 → 공유 인프라 시작 → Blue-Green 배포 → 이미지 정리

---

## 10. 테스트 구조

| 파일 | 테스트 대상 |
|------|------------|
| `tests/api/test_health.py` | `GET /health` → 200 `{"status": "ok"}` |
| `tests/api/test_internal_auth.py` | 키 없는 내부 엔드포인트 → 403 |
| `tests/graph/test_agent_graph.py` | 메타데이터 추출, 중복 제거, AgentGraphWorkflow.run() 구조 |
| `tests/llm/tools/test_product_search_tool.py` | 툴 응답 포맷, 빈 결과 처리 |
| `tests/rag/test_product_document.py` | 문서에 제품명, 원산지, 플레이버 포함 확인 |
| `tests/rag/test_product_repository_merge.py` | SQL 조인 결과 → 원두 배열 병합 |
| `tests/ml/test_metrics.py` | exact_match 1.0/0.0 반환 확인 |
| `tests/services/test_training_service.py` | 경로 순회 공격 (`../../`) → 400 HTTPException |

---

## 11. 에이전트 확장 로드맵

| 단계 | 추가할 것 | 작업 범위 |
|------|-----------|-----------|
| 완료 | `search_products` 툴 | 기존 RAG 파이프라인을 툴로 래핑 |
| 다음 | `search_website_docs` 구현 | 웹사이트 메뉴얼 Qdrant 컬렉션 구축 + 툴 함수 구현 |
| 이후 | `get_order_status` 등 | 툴 함수 추가 + 에이전트 프롬프트 보강 |

### 웹사이트 메뉴얼 RAG 추가 시 변경 범위

1. 메뉴얼 문서를 Qdrant 별도 컬렉션으로 인덱싱
2. `src/llm/tools/doc_search_tool.py` TODO 구현 (현재 스텁)
3. `agent_prompt.py` 예시 보강

`agent_graph.py`와 `chat_service.py`는 변경 불필요.

---

## 12. ML 파이프라인 현황

### 구현 완료

- JSONL 데이터셋 로더
- Instruction/Input/Response 포맷 변환
- `exact_match` 평가 메트릭
- CLI 훈련 스크립트 (`scripts/train.py`)

### 스텁 (미구현)

| 컴포넌트 | 파일 | 현황 |
|----------|------|------|
| SFT 훈련 | `src/ml/trainers/sft_trainer.py` | preview 파일만 생성 |
| 로컬 추론 | `src/ml/inference/predictor.py` | 스텁 응답 반환 |

### 향후 확장 계획

- `[ml]` extras: transformers, PEFT, TRL, sentence-transformers, datasets, accelerate
- LoRA/QLoRA 파인튜닝 통합 예정 구조

---

## 13. 현재 구조의 강점 및 개선 포인트

### 강점

- **에이전트 기반 멀티툴**: 복합 질문(제품 추천 + 사이트 안내)을 단일 흐름에서 처리
- **툴 추가 = 기능 추가**: 새 지식 소스는 툴 함수 1개 + 프롬프트 보강으로 완결
- **지연 초기화**: 앱 시작 속도 향상, 불필요한 연결 방지
- **N+1 방지**: 일괄 쿼리 + Python 머지 패턴
- **제로다운타임 배포**: Blue-Green + 헬스체크 기반 자동 롤백
- **보안 기초**: 인증, 경로 검증, 읽기 전용 DB 계정

### 개선 포인트

- **워커 미구현**: `apps/worker/main.py` 플레이스홀더 상태. 인덱싱/훈련 작업이 FastAPI BackgroundTask로 실행되어 서버 재시작 시 유실 가능
- **ML 파이프라인 스텁**: SFT 훈련, 로컬 추론 미구현
- **에이전트 Latency**: 툴 호출 수만큼 LLM 라운드트립 증가. 단순 일반 질문에도 툴 판단 LLM 호출 1회 발생
- **메뉴얼 RAG 미구현**: `search_website_docs` 스텁 상태, 실제 응답 불가
- **모니터링 부재**: Prometheus, Grafana 등 메트릭 수집 없음
- **로깅 최소화**: basicConfig 수준, 구조화 로깅(structlog 등) 미적용
- **recursion_limit=10 고정**: 툴 호출이 많은 복잡한 질문에서 제한에 걸릴 수 있음

---

## 14. 로컬 실행 방법

### Docker Compose (권장)

```bash
cp .env.example .env
# .env 편집 (OpenAI API 키 등)
docker compose up -d
```

### 직접 실행

```bash
pip install -e ".[dev]"
uvicorn apps.api.main:app --reload
```

### 제품 인덱싱

```bash
python scripts/index_products.py
```

### 테스트 실행

```bash
pytest tests/ -v
```

---

## 15. 에이전트 시스템 프롬프트 설계

`src/llm/prompts/agent_prompt.py` 구조:

```
역할: Baristation 커피 전문 AI 어시스턴트
언어: 한국어 (요청 시 변경 가능)

툴 사용 원칙:
- 제품 추천·비교·탐색         → search_products
- 사이트 이용·주문·배송       → search_website_docs
- 두 정보 모두 필요한 질문     → 두 툴 모두 호출 후 통합 답변
- 커피 일반 지식              → 툴 없이 직접 답변

답변 원칙:
- search_products 결과에 있는 제품만 추천
- 맛 특성(산미/단맛/바디/밸런스), 원산지, 플레이버 노트로 추천 이유 설명
- 정보 부족 시 솔직하게 고지
```
