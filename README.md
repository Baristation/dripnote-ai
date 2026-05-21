# dripnote-ai


- `apps/api`: 외부에서 호출하는 API 서버
- `src/services`: 실제 동작을 조립하는 서비스 계층
- `src/llm`: LLM 호출 관련 코드
- `src/graph`: LangGraph 흐름 제어
- `src/rag`: 문서 검색과 벡터 저장소
- `src/ml`: 학습, 전처리, 평가
- `scripts`: 터미널에서 직접 실행하는 스크립트
- `data`: 학습용 데이터 원본/가공본
- `models`: 학습 결과물 저장 폴더

## 폴더 구조 설명

```text
dripnote-ai/
|- apps/
|  |- api/
|  |  |- main.py              # FastAPI 시작점
|  |  \- routes/              # API 주소별 파일
|  \- worker/                 # 나중에 비동기 작업 처리할 때 사용
|- src/
|  |- core/                   # 설정, 로깅, 공통 코드
|  |- services/               # 여러 모듈을 묶어 실제 기능 수행
|  |- llm/                    # LangChain, 프롬프트, 모델 클라이언트
|  |- graph/                  # LangGraph 상태/노드/워크플로우
|  |- rag/                    # Qdrant 인덱싱, 검색 문서 생성, 벡터 검색
|  |- ml/                     # 학습 데이터, 전처리, 트레이너, 평가
|  \- db/                     # DB 관련 코드 자리
|- scripts/                   # 학습/인덱싱 명령 실행 파일
|- data/
|  |- raw/                    # 원본 데이터
|  |- processed/              # 전처리된 데이터
|  \- external/               # 외부 수집 데이터
|- models/
|  |- checkpoints/            # 학습 중간 저장물
|  |- exported/               # 배포용 모델
|  \- tokenizers/             # 토크나이저 파일
\- tests/                     # 테스트 코드
```

## 요청이 들어왔을 때 흐름

사용자가 `/api/chat`을 호출하면 보통 아래 순서로 흘러갑니다.

```text
apps/api/routes/chat.py
-> src/services/chat_service.py
-> src/graph/workflows/chat_graph.py
-> src/llm/chains/answer_chain.py
-> 실제 LLM 호출
```

즉,

- `route`: HTTP 요청 받기
- `service`: 어떤 기능을 쓸지 결정
- `graph`: 단계 순서 제어
- `chain`: 프롬프트 조합 후 모델 호출

## RAG


- `src/rag/documents`: 상품 데이터를 검색용 문서와 Qdrant payload로 변환
- `src/rag/vectorstores/qdrant_store.py`: Qdrant collection 생성, upsert, search
- `src/rag/pipelines/product_index_pipeline.py`: 백엔드 MySQL read-only 데이터 인덱싱
- `src/graph/workflows/rag_graph.py`: LangGraph 기반 RAG 질의 흐름


```text
백엔드 MySQL:8005 read-only
-> Product/Bean/Roaster/FlavorNote 조회
-> 검색용 문서 생성
-> OpenAI embedding
-> Qdrant upsert

질문 입력
-> LangGraph
-> Qdrant semantic search
-> MySQL read-only 상세 보강
-> LLM 답변
```

## 학습 코드

- `src/ml/datasets`: JSONL 같은 학습 데이터 읽기
- `src/ml/preprocessing`: instruction 형식으로 변환
- `src/ml/trainers`: 실제 학습 로직
- `src/ml/inference`: 학습된 모델 추론
- `src/ml/evaluation`: 평가 함수
- `scripts/train.py`: 터미널에서 학습 시작

현재 `sft_trainer.py`는 진짜 파인튜닝까지 돌리는 상태는 아니고,
우선 데이터가 잘 들어오는지 확인하는 스텁 형태입니다.


## 흐름
1. `apps/api/main.py`
서버가 어떻게 시작되는지 봅니다.

2. `apps/api/routes/chat.py`
어떤 요청을 받는지 봅니다.

3. `src/services/chat_service.py`
채팅 요청이 실제로 어디로 흘러가는지 봅니다.

4. `src/graph/workflows/chat_graph.py`
LangGraph가 어떤 순서로 실행되는지 봅니다.

5. `src/llm/chains/answer_chain.py`
마지막으로 LLM 호출이 어떻게 되는지 봅니다.

## 실행 예시

가상환경과 패키지 설치 후:

```bash
uvicorn apps.api.main:app --reload
```

학습 스크립트 예시:

```bash
python scripts/train.py --train-path data/processed/train.jsonl --output-dir models/checkpoints/demo-run
```

상품 Qdrant 인덱싱 예시:

```bash
python scripts/index_products.py
```

