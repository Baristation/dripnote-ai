# dripnote-ai 구조 분석 리포트

작성일: 2026-05-06

## 1. 프로젝트 개요

`dripnote-ai`는 Baristation 서비스의 AI 서버로 보이며, 커피 상품 추천/응답을 위한 LLM 호출, LangGraph 기반 RAG 워크플로우, Qdrant 벡터 검색, 백엔드 MySQL read-only 조회, Redis 캐시, 학습 스텁 코드를 포함한다.

핵심 목적은 다음과 같다.

- FastAPI로 AI API를 제공한다.
- 일반 LLM-only 채팅과 Qdrant 기반 RAG 채팅을 분리해서 처리한다.
- 백엔드 MySQL의 상품, 원두, 로스터, 향미 데이터를 읽어 Qdrant에 인덱싱한다.
- 검색된 상품 id를 다시 MySQL에서 조회해 최신 상세 정보를 보강한다.
- 향후 SFT, 배치 작업, 캐시, 비동기 worker 확장을 위한 기본 구조를 마련한다.

현재 구현 상태는 "동작 가능한 RAG/LLM 서버 스캐폴드 + 일부 실제 연동 코드 + 학습 스텁"에 가깝다. RAG 인덱싱과 검색 경로는 비교적 구체적으로 구현되어 있고, ML 학습은 실제 파인튜닝이 아니라 입력 데이터 미리보기 파일을 생성하는 수준이다.

## 2. 기술 스택

`pyproject.toml` 기준 주요 의존성은 다음과 같다.

| 영역 | 사용 기술 |
| --- | --- |
| API 서버 | FastAPI, Uvicorn |
| 설정 | pydantic-settings |
| LLM | LangChain, langchain-openai |
| 그래프 오케스트레이션 | LangGraph |
| 벡터 DB | Qdrant |
| 관계형 DB | SQLAlchemy, PyMySQL |
| 캐시/세션 저장소 | Redis |
| 재시도/업로드 지원 | tenacity, python-multipart |
| 테스트/개발 | pytest, httpx, ruff |
| 선택 ML 의존성 | sentence-transformers, datasets, transformers, accelerate, peft, trl |

Python 버전은 `>=3.11`을 요구한다.

## 3. 최상위 디렉터리 구조

```text
dripnote-ai/
|- apps/
|  |- api/                    # FastAPI 앱과 HTTP 라우터
|  \- worker/                 # 향후 큐/비동기 작업용 placeholder
|- src/
|  |- core/                   # 설정, Redis, 로깅 등 공통 기반
|  |- db/                     # MySQL 연결과 read repository
|  |- graph/                  # LangGraph 상태, 노드, 워크플로우
|  |- llm/                    # OpenAI client, chain, prompt
|  |- ml/                     # 데이터셋, 전처리, 학습, 추론, 평가
|  |- rag/                    # 문서 생성, Qdrant store, 인덱싱 pipeline
|  \- services/               # API와 내부 기능을 연결하는 서비스 계층
|- scripts/                   # CLI 실행 진입점
|- data/
|  |- raw/                    # 원본 데이터
|  |- processed/              # 전처리 데이터
|  \- external/               # 외부 데이터
|- models/
|  |- checkpoints/            # 학습 중간 산출물
|  |- exported/               # 배포 모델
|  \- tokenizers/             # tokenizer 저장 위치
|- tests/                     # API, graph, ML, RAG 단위 테스트
|- Dockerfile                 # FastAPI 컨테이너 이미지
|- docker-compose.yml         # ai-api, qdrant, redis 로컬 구성
|- pyproject.toml             # 패키지/의존성/테스트 설정
\- README.md                  # 기본 구조와 실행 예시
```

`.git`, `.idea`, `.claude`, `__pycache__`류 파일은 개발 환경/도구 산출물로, 런타임 구조 분석에서는 제외하는 것이 좋다.

## 4. API 계층

### 4.1 `apps/api/main.py`

FastAPI 애플리케이션 시작점이다.

- `get_settings()`로 환경 설정을 읽는다.
- FastAPI 앱 제목을 `settings.app_name`으로 설정한다.
- `chat`, `rag`, `training` 라우터를 모두 `/api` prefix로 연결한다.
- `/health` 엔드포인트가 `{"status": "ok"}`를 반환한다.

등록되는 라우터는 다음과 같다.

```text
GET  /health
POST /api/chat
POST /api/rag/index/products
POST /api/train
```

### 4.2 `apps/api/routes/chat.py`

채팅 요청을 받는 라우터다.

요청 모델:

```text
ChatRequest
|- message: str, required, min_length=1
\- use_rag: bool, default=False
```

응답 모델:

```text
ChatResponse
|- answer: str
|- workflow: str
|- recommended_product_ids: list[int]
\- sources: list[ChatSource]
```

`use_rag=false`이면 LLM-only 경로를 사용하고, `use_rag=true`이면 Qdrant + MySQL 보강 기반 RAG 경로를 사용한다.

### 4.3 `apps/api/routes/rag.py`

상품 데이터를 Qdrant에 재색인하는 API다.

```text
POST /api/rag/index/products
```

내부적으로 `ProductIndexPipeline().run()`을 호출하고, 인덱싱된 상품 수를 반환한다. MySQL read-only 데이터에 접근하고 OpenAI embedding을 생성하므로, 실제 실행에는 DB, Qdrant, OpenAI API 설정이 필요하다.

### 4.4 `apps/api/routes/training.py`

학습 작업 시작 API다.

요청 모델:

```text
TrainRequest
|- train_path: str
\- output_dir: str
```

현재는 실제 장기 학습 job queue가 아니라 `TrainingService.start_training()`을 동기 호출한다. 결과로 `{"status": "started", "job": output_dir_name}` 형태를 반환하지만, 내부 구현은 preview 파일 생성 스텁이다.

## 5. 서비스 계층

### 5.1 `src/services/chat_service.py`

채팅 기능의 중심 조립 계층이다.

보유 구성요소:

- `ChatGraphWorkflow`: 일반 LLM-only 경로에서 question/context를 정리한다.
- `RagGraphWorkflow`: RAG 경로 전체를 실행한다.
- `AnswerChain`: OpenAI Chat 모델 호출 chain. API key가 필요한 시점을 늦추기 위해 lazy initialization을 사용한다.

분기 흐름:

```text
generate_reply(message, use_rag=False)
|- use_rag=True
|  \- RagGraphWorkflow.run(question=message)
|     \- answer, recommended_product_ids, sources 반환
\- use_rag=False
   |- ChatGraphWorkflow.run(message, context="")
   \- AnswerChain.invoke(question, context)
```

### 5.2 `src/services/training_service.py`

학습 요청을 `SFTTrainerService`로 위임한다.

- 문자열 경로를 `Path`로 변환한다.
- `trainer.train(dataset_path, output_dir)`를 호출한다.
- 반환값으로 output directory 이름을 job id처럼 사용한다.

### 5.3 `src/services/cache_service.py`

Redis JSON 캐시 유틸리티다.

- `get_json(namespace, key)`: Redis 문자열 값을 JSON dict로 역직렬화한다.
- `set_json(namespace, key, value, ttl_seconds)`: TTL이 있는 JSON 캐시를 저장한다.
- key 형식은 `{redis_key_prefix}:{namespace}:{key}`다.

현재 주요 RAG/채팅 경로에서 직접 사용되지는 않지만, LLM 결과 캐시, 세션, job status, rate limit 등으로 확장하기 좋은 위치다.

## 6. 설정과 인프라

### 6.1 `src/core/config.py`

`pydantic-settings` 기반 설정 객체를 정의한다. `.env` 파일을 읽으며 기본값도 갖고 있다.

주요 설정 그룹:

- 앱: `app_name`, `app_env`
- OpenAI: `openai_api_key`, `openai_model`, `embedding_model`
- 학습: `train_device`
- Qdrant: `qdrant_url`, `qdrant_api_key`, `qdrant_collection`, `qdrant_vector_size`, `qdrant_top_k`
- Redis: `redis_host`, `redis_port`, `redis_db`, `redis_password`, `redis_key_prefix`
- 백엔드 MySQL: `backend_mysql_host`, `backend_mysql_port`, `backend_mysql_database`, `backend_mysql_user`, `backend_mysql_password`

`get_settings()`는 `lru_cache`로 캐시되어 프로세스 안에서 설정 객체를 재사용한다.

### 6.2 `src/core/redis.py`

Redis client factory다.

- `redis.Redis(...)`를 생성한다.
- `decode_responses=True`로 문자열 응답을 받는다.
- `get_redis_client()`도 `lru_cache`로 캐시된다.

### 6.3 `src/db/mysql.py`

SQLAlchemy engine factory다.

- `mysql+pymysql` URL을 설정값으로 구성한다.
- 백엔드 MySQL의 read-only 계정 접속을 전제로 한다.
- `pool_pre_ping=True`, `pool_recycle=1800`으로 장기 실행 서버의 연결 안정성을 고려한다.

## 7. LLM 계층

### 7.1 `src/llm/clients/openai_client.py`

OpenAI 모델 생성 함수가 있다.

- `build_chat_model()`: `ChatOpenAI`를 생성한다. 기본 모델은 `gpt-4.1-mini`, temperature는 0이다.
- `build_embeddings()`: `OpenAIEmbeddings`를 생성한다. 기본 embedding 모델은 `text-embedding-3-small`이다.

기본 Qdrant vector size는 1536으로, `text-embedding-3-small`의 차원과 맞춰져 있다.

### 7.2 `src/llm/chains/answer_chain.py`

최종 답변 생성 chain이다.

구성:

- system prompt: `src/llm/prompts/chat_prompt.py`의 `SYSTEM_PROMPT`
- human prompt: `Question: {question}\n\nContext:\n{context}`
- prompt와 chat model을 LangChain pipe로 연결한다.

`invoke(question, context)`는 LLM 응답의 `content`를 문자열로 반환한다.

### 7.3 `src/llm/prompts/chat_prompt.py`

시스템 프롬프트는 짧고 범용적이다.

- backend assistant 역할
- 명확하고 간결하게 답변
- context가 있으면 사용
- context가 없으면 일반 추론으로 답변하되 필요한 경우 가정을 밝힘

현재 프롬프트는 커피 추천 도메인 특화 지시가 약하다. RAG 품질을 올리려면 추천 기준, 말투, source 사용 규칙, 환각 방지 규칙을 더 구체화하는 것이 좋다.

## 8. LangGraph 구조

### 8.1 일반 채팅 그래프

파일:

- `src/graph/state/chat_state.py`
- `src/graph/nodes/prepare_context.py`
- `src/graph/workflows/chat_graph.py`

상태:

```text
ChatState
|- question: str
\- context: str
```

그래프:

```text
START
-> prepare_context
```

`prepare_context`는 context 앞뒤 공백을 제거하고, context가 있으면 `Retrieved context:` prefix를 붙인다. 현재 LLM-only 경로에서는 빈 context를 넘기므로 사실상 question 유지용 얇은 그래프다.

### 8.2 RAG 그래프

파일:

- `src/graph/state/rag_state.py`
- `src/graph/nodes/normalize_query.py`
- `src/graph/nodes/retrieve_qdrant.py`
- `src/graph/nodes/fetch_products.py`
- `src/graph/nodes/build_context.py`
- `src/graph/nodes/generate_answer.py`
- `src/graph/workflows/rag_graph.py`

상태:

```text
RagState
|- question: str
|- normalized_question: str
|- qdrant_hits: list[dict]
|- product_ids: list[int]
|- products: list[dict]
|- context: str
|- answer: str
|- recommended_product_ids: list[int]
\- sources: list[dict]
```

그래프:

```text
START
-> normalize_query
-> retrieve_qdrant
-> fetch_products
-> build_context
-> generate_answer
-> END
```

노드 역할:

| 노드 | 역할 |
| --- | --- |
| `normalize_query` | 사용자 질문의 앞뒤 공백과 중복 공백을 정리한다. |
| `retrieve_qdrant` | 정규화된 질문을 embedding으로 변환하고 Qdrant에서 상품 point를 검색한다. |
| `fetch_products` | Qdrant payload의 `productId` 목록으로 MySQL 최신 상품/향미 데이터를 조회한다. |
| `build_context` | 상품별 문서 문자열을 만들고 API 응답용 source 목록을 구성한다. |
| `generate_answer` | 조립된 context와 원 질문을 `AnswerChain`에 넣어 최종 답변을 생성한다. |

## 9. RAG 계층

### 9.1 MySQL read repository

파일: `src/db/repositories/product_read_repository.py`

주요 쿼리:

- `PRODUCT_BASE_QUERY`: product, roasters, bean_product, bean을 join해 상품/원두/로스터 기본 정보를 조회한다.
- `PRODUCT_BY_IDS_QUERY`: 특정 product id 목록만 조회한다.
- `PRODUCT_FLAVORS_QUERY`: product_flavor_note와 flavor_note를 join해 향미 정보를 조회한다.

주요 함수:

- `fetch_products_for_indexing()`: 전체 상품을 Qdrant 재색인용으로 조회한다.
- `fetch_products_by_ids(product_ids)`: 검색 결과 상품 id 목록을 최신 DB 정보로 보강한다.
- `fetch_flavors_by_product_ids(product_ids)`: 여러 상품의 향미를 한 번에 조회해 product_id 기준 dict로 묶는다.

현재 쿼리는 하나의 상품이 여러 bean과 연결될 수 있을 때 product row가 중복될 가능성이 있다. Qdrant point id를 `product_id`로 쓰므로 최종 upsert는 같은 id를 덮어쓰지만, 문서 내용이 마지막 row 기준으로 치우칠 수 있다. 다중 원두 상품이 중요하다면 product_id 기준 aggregation이 필요하다.

### 9.2 상품 문서 생성

파일: `src/rag/documents/product_document.py`

`build_product_document(product, flavors)`는 embedding과 LLM context에 같이 쓰이는 텍스트 문서를 만든다.

포함 정보:

- 상품명 ko/en
- 로스터명 ko/en
- 원두명 ko/en
- 산지, 지역, 가공, 품종, 고도
- 로스팅 레벨, Agtron
- 산미, 단맛, 바디, 밸런스
- 향미 카테고리, 향미 노트
- 설명, 상품 URL

`build_product_payload(product, flavors, document)`는 Qdrant payload를 만든다.

주요 payload 필드:

- `productId`, `beanId`, `roasterId`
- 상품명/로스터명 ko/en
- roast level, origin, region
- flavor categories, flavor notes
- `updatedAt`
- 검색 문서 원문 `document`

### 9.3 Qdrant store

파일: `src/rag/vectorstores/qdrant_store.py`

주요 함수:

- `get_qdrant_client()`: 설정 기반 QdrantClient 생성
- `ensure_collection()`: collection이 없으면 cosine distance와 설정된 vector size로 생성
- `upsert_product_vectors(points)`: 상품 point upsert
- `search_products(query_vector, limit=None)`: query vector로 검색 후 `id`, `score`, `payload` dict 목록 반환

기본 collection 이름은 `baristation-products`, 기본 top-k는 5다.

주의점:

- `ensure_collection()`은 collection 존재 여부만 확인하고 vector size 변경은 처리하지 않는다.
- embedding 모델을 변경하면 `qdrant_vector_size`와 기존 collection schema가 맞는지 확인해야 한다.
- qdrant-client 최신 버전에서는 `client.search`가 deprecate될 수 있으므로 버전 업그레이드 시 확인이 필요하다.

### 9.4 상품 인덱싱 pipeline

파일: `src/rag/pipelines/product_index_pipeline.py`

흐름:

```text
fetch_products_for_indexing()
-> product_ids 추출
-> fetch_flavors_by_product_ids(product_ids)
-> build_embeddings()
-> 상품별 build_product_document()
-> embeddings.embed_query(document)
-> build_product_payload()
-> PointStruct(id=product_id, vector=vector, payload=payload)
-> upsert_product_vectors(points)
```

빈 데이터면 Qdrant upsert를 호출하지 않고 0을 반환한다.

## 10. ML/학습 계층

### 10.1 데이터셋

파일: `src/ml/datasets/jsonl_dataset.py`

`load_jsonl_dataset(path)`가 JSONL 파일을 한 줄씩 읽어 dict 목록으로 반환한다. 빈 줄은 건너뛴다.

### 10.2 전처리

파일: `src/ml/preprocessing/format_supervised.py`

`to_instruction_text(record)`가 `instruction`, `input`, `output` 필드를 아래 형식으로 변환한다.

```text
Instruction: ...
Input: ...
Response: ...
```

### 10.3 학습

파일: `src/ml/trainers/sft_trainer.py`

현재 `SFTTrainerService.train()`은 실제 모델 학습을 수행하지 않는다.

동작:

- output directory 생성
- JSONL dataset 로드
- 앞 10개 record를 instruction text로 변환
- `training_preview.txt` 저장

`pyproject.toml`의 `ml` extra에는 transformers, peft, trl 등이 준비되어 있으므로 추후 LoRA/SFT 구현을 붙이기 위한 의도가 있다.

### 10.4 추론

파일: `src/ml/inference/predictor.py`

`LocalPredictor`는 현재 stub이다.

```text
[stub prediction from {model_dir.name}] {text}
```

형태로 입력을 그대로 포함한 문자열을 반환한다.

### 10.5 평가

파일: `src/ml/evaluation/metrics.py`

`exact_match(prediction, reference)`만 구현되어 있다.

- strip 후 완전 일치하면 1.0
- 다르면 0.0

## 11. CLI 스크립트

### 11.1 `scripts/index_products.py`

상품 Qdrant 인덱싱을 수동 실행하는 CLI다.

```bash
python scripts/index_products.py
```

실행 결과로 `indexed {count} products`를 출력한다.

### 11.2 `scripts/train.py`

학습 스텁 실행 CLI다.

```bash
python scripts/train.py --train-path data/processed/train.jsonl --output-dir models/checkpoints/demo-run
```

내부적으로 `TrainingService.start_training()`을 호출하고, 현재는 `training_preview.txt`를 생성한다.

## 12. Docker/Compose 구성

### 12.1 `Dockerfile`

런타임 이미지는 `python:3.11-slim` 기반이다.

주요 단계:

- `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`
- 작업 디렉터리 `/app`
- `curl`, `build-essential` 설치
- `pyproject.toml`, `README.md`, `apps`, `src`, `scripts` 복사
- `pip install ".[dev]"`
- 8000 포트 expose
- `/health` Docker healthcheck
- `uvicorn apps.api.main:app --host 0.0.0.0 --port 8000`

개발 편의상 dev extra까지 설치한다.

### 12.2 `docker-compose.yml`

서비스:

| 서비스 | 역할 | 포트 |
| --- | --- | --- |
| `ai-api` | FastAPI AI 서버 | 8000:8000 |
| `qdrant` | RAG vector DB | 6333:6333, 6334:6334 |
| `redis` | 캐시/세션/job status용 Redis | 6379:6379 |

볼륨:

- `qdrant_data`
- `redis_data`

`ai-api`는 Qdrant healthcheck 통과와 Redis 시작 이후 올라오도록 설정되어 있다. 백엔드 MySQL 접근을 위해 `host.docker.internal:host-gateway`도 추가되어 있다.

주의: 현재 `docker-compose.yml`과 `Dockerfile`의 주석 일부는 인코딩이 깨져 보인다. 파일 자체 인코딩 또는 에디터 저장 인코딩을 UTF-8로 정리하는 것이 좋다.

## 13. 테스트 구조

현재 테스트는 네 영역으로 나뉜다.

```text
tests/
|- api/test_health.py
|- graph/test_chat_graph.py
|- ml/test_metrics.py
\- rag/test_product_document.py
```

테스트 내용:

- `/health`가 200과 `{"status": "ok"}`를 반환하는지 확인
- `ChatGraphWorkflow`가 question을 유지하고 context를 포함하는지 확인
- `exact_match` metric 확인
- 상품 document/payload가 핵심 필드를 포함하는지 확인

현재 테스트는 외부 의존성 없는 단위/스모크 테스트 중심이다. Qdrant, MySQL, OpenAI 연동은 테스트되지 않는다.

## 14. 주요 실행 흐름

### 14.1 LLM-only 채팅

```text
POST /api/chat {"message": "...", "use_rag": false}
-> apps/api/routes/chat.py
-> ChatService.generate_reply(use_rag=False)
-> ChatGraphWorkflow.run(message, context="")
-> prepare_context
-> AnswerChain.invoke(question, context)
-> OpenAI ChatOpenAI
-> ChatResponse(workflow="llm-only")
```

### 14.2 RAG 채팅

```text
POST /api/chat {"message": "...", "use_rag": true}
-> apps/api/routes/chat.py
-> ChatService.generate_reply(use_rag=True)
-> RagGraphWorkflow.run(question)
-> normalize_query
-> OpenAIEmbeddings.embed_query(question)
-> Qdrant search
-> productId 추출
-> MySQL fetch_products_by_ids
-> MySQL fetch_flavors_by_product_ids
-> build_product_document
-> sources/recommended_product_ids 구성
-> AnswerChain.invoke(question, context)
-> ChatResponse(workflow="rag-qdrant")
```

### 14.3 상품 인덱싱

```text
POST /api/rag/index/products
또는 python scripts/index_products.py
-> ProductIndexPipeline.run()
-> MySQL 전체 상품 조회
-> MySQL 향미 조회
-> 상품별 document 생성
-> OpenAI embedding 생성
-> Qdrant PointStruct 생성
-> Qdrant upsert
```

### 14.4 학습 스텁

```text
POST /api/train
또는 python scripts/train.py --train-path ... --output-dir ...
-> TrainingService.start_training
-> SFTTrainerService.train
-> JSONL 로드
-> 앞 10개 record instruction text 변환
-> training_preview.txt 저장
```

## 15. 데이터/모델 디렉터리 의도

`data`와 `models`는 `.gitkeep`만 추적하고 실제 데이터/모델 산출물은 `.gitignore`로 제외한다.

```text
data/raw/*         # 원본 데이터 제외
data/processed/*   # 전처리 데이터 제외
data/external/*    # 외부 데이터 제외
models/checkpoints/*
models/exported/*
models/tokenizers/*
```

따라서 민감 데이터, 대용량 학습 파일, 모델 체크포인트가 git에 들어가지 않도록 설계되어 있다.

## 16. 현재 강점

- API, service, graph, llm, rag, ml 계층이 분리되어 있어 확장 방향이 명확하다.
- OpenAI client, Redis client, MySQL engine이 lazy/cached factory로 구성되어 import 시점 부작용을 줄인다.
- RAG 그래프가 단방향으로 단순해 테스트와 노드 추가가 쉽다.
- Qdrant payload와 MySQL 재조회가 분리되어 검색 metadata와 최신 상세 데이터의 역할이 구분된다.
- 외부 의존성이 필요한 RAG/LLM 경로와 외부 의존성 없는 기본 테스트가 분리되어 있다.

## 17. 주의점과 개선 후보

1. `docker-compose.yml`, `Dockerfile`, 일부 route/service 파일의 주석이 깨져 보인다. UTF-8 재저장이 필요하다.

2. `ChatService` 생성 시 `RagGraphWorkflow()`도 즉시 생성된다. RAG graph 자체는 API key를 요구하지 않지만, 더 엄격한 lazy 구성을 원하면 use_rag 호출 시점에 생성할 수 있다.

3. `generate_answer` 노드는 요청마다 `AnswerChain()`을 새로 만든다. LLM client 재사용이나 graph-level dependency injection을 고려할 수 있다.

4. RAG 검색 결과가 없을 때 fallback 정책이 없다. 현재는 빈 context로 LLM이 답변할 가능성이 있어, "검색된 상품이 없다"는 명확한 응답이나 일반 답변 fallback 정책을 정해야 한다.

5. `PRODUCT_BASE_QUERY`는 product와 bean의 N:M 관계 때문에 같은 product_id가 여러 row로 나올 수 있다. 다중 원두 상품이 있다면 문서 병합 로직이 필요하다.

6. `build_context`는 MySQL 조회 결과 순서를 그대로 사용한다. Qdrant score 순서를 보존하려면 `product_ids` 또는 score 기준으로 정렬하는 로직이 필요할 수 있다.

7. Qdrant collection schema 변경 대응이 없다. embedding 모델 변경 시 collection 재생성/마이그레이션 절차가 필요하다.

8. API layer에 인증/권한 제어가 없다. 특히 `/api/rag/index/products`, `/api/train`은 운영 환경에서 보호되어야 한다.

9. `/api/train`은 "started"를 반환하지만 실제로는 동기 실행이다. 장기 작업이 되면 worker/queue/job status 구조가 필요하다.

10. `src/db/models`, `src/rag/embeddings`, `src/rag/loaders`는 현재 비어 있는 확장 자리다. 실제 구현 전까지는 의도만 문서화하거나 제거 여부를 결정할 수 있다.

11. 테스트는 핵심 외부 연동을 mock으로 검증하지 않는다. RAG graph 노드별 mock 테스트와 ChatService 분기 테스트를 추가하면 회귀 방지에 도움이 된다.

12. 커피 추천 도메인 프롬프트가 아직 얕다. 추천 기준, 답변 형식, source 사용 규칙, 불확실성 처리 규칙을 강화하면 결과 품질이 좋아질 수 있다.

## 18. 추천 후속 작업

우선순위가 높은 작업은 다음 순서가 적절하다.

1. 깨진 한글 주석 인코딩 정리
2. RAG 검색 결과 없음/fallback 정책 구현
3. `ChatService`, `RagGraphWorkflow`, RAG 노드 mock 테스트 추가
4. Qdrant 검색 결과 순서 보존 로직 추가
5. product_id 중복 row 병합 또는 SQL aggregation 처리
6. 운영 보호가 필요한 API에 인증 또는 내부망 제한 추가
7. 학습 API를 실제 비동기 job 구조로 변경
8. 커피 추천 도메인 프롬프트 고도화

## 19. 빠른 명령 모음

로컬 서버 실행:

```bash
uvicorn apps.api.main:app --reload
```

Docker Compose 실행:

```bash
docker compose up --build
```

상품 인덱싱:

```bash
python scripts/index_products.py
```

학습 스텁:

```bash
python scripts/train.py --train-path data/processed/train.jsonl --output-dir models/checkpoints/demo-run
```

테스트:

```bash
pytest
```

## 20. 한 줄 결론

`dripnote-ai`는 Baristation 상품 데이터를 기반으로 한 커피 추천형 RAG AI 서버의 초안이다. API와 LangGraph/RAG 골격은 이미 비교적 선명하며, 운영 품질을 위해서는 인코딩 정리, fallback 정책, 테스트 보강, 인증, 중복 상품 병합, 프롬프트 고도화가 다음 핵심 과제다.
