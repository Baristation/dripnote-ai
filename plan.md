# ReAct Agent 기반 멀티툴 챗봇 구현 계획

## 왜 라우터가 아닌 에이전트인가

라우터는 질문을 하나의 파이프라인으로 보낸다. 에이전트는 LLM이 직접 어떤 툴을 몇 번 쓸지 결정한다.

```
[라우터]
"이 원두 설명해주고 구매 방법도 알려줘"
  → classify: product_rec OR website_help  ← 둘 중 하나만 선택 가능

[에이전트]
"이 원두 설명해주고 구매 방법도 알려줘"
  → search_products("원두") 호출
  → search_website_docs("구매 방법") 호출
  → 두 결과 합쳐서 최종 답변
```

웹사이트 메뉴얼 RAG, 에이전트 기능 추가 계획을 감안하면 처음부터 에이전트로 가는 것이 맞다.
새 지식 소스 추가 = **툴 함수 1개 추가**로 완결.

---

## 목표 흐름

```
[현재]
Client → POST /api/chat { message, use_rag: true/false }
       → ChatService가 분기
       → RagGraphWorkflow | ChatGraphWorkflow

[목표]
Client → POST /api/chat { message }
       → AgentGraph (ReAct 루프)
             LLM이 판단:
             - search_products 호출    (제품 추천/탐색)
             - search_website_docs 호출 (사이트 이용 안내)  ← 메뉴얼 추가 시 활성화
             - 툴 없이 직접 답변        (일반 커피 지식)
```

---

## 확장 로드맵

| 단계 | 추가할 것 | 작업 범위 |
|------|-----------|-----------|
| 현재 | `search_products` 툴 | 기존 RAG 파이프라인을 툴로 래핑 |
| 다음 | `search_website_docs` 툴 | Qdrant 메뉴얼 컬렉션 + 툴 함수 1개 |
| 이후 | `get_order_status` 등 | 툴 함수 추가, 에이전트 프롬프트 보강 |

---

## 구현 범위

### 새로 만들 파일

| 파일 | 역할 |
|------|------|
| `src/llm/prompts/agent_prompt.py` | ReAct 에이전트 시스템 프롬프트 |
| `src/llm/tools/product_search_tool.py` | `search_products` 툴 (Qdrant + MySQL) |
| `src/llm/tools/doc_search_tool.py` | `search_website_docs` 툴 스텁 (메뉴얼 추가 시 구현) |
| `src/graph/workflows/agent_graph.py` | `create_react_agent` 래퍼 |
| `tests/llm/tools/test_product_search_tool.py` | 툴 단위 테스트 |
| `tests/graph/test_agent_graph.py` | 에이전트 통합 테스트 |

### 수정할 파일

| 파일 | 변경 내용 |
|------|-----------|
| `src/services/chat_service.py` | 두 워크플로우 → AgentGraph 단일 진입점 |
| `apps/api/routes/chat.py` | `ChatRequest.use_rag` 필드 제거 |

### 삭제할 파일 (기능이 툴로 흡수됨)

| 파일 | 이유 |
|------|------|
| `src/graph/workflows/chat_graph.py` | 에이전트가 툴 없이 직접 답변으로 대체 |
| `src/graph/workflows/rag_graph.py` | `search_products` 툴로 대체 |
| `src/graph/nodes/normalize_query.py` | 툴 내부로 흡수 |
| `src/graph/nodes/retrieve_qdrant.py` | 툴 내부로 흡수 |
| `src/graph/nodes/fetch_products.py` | 툴 내부로 흡수 |
| `src/graph/nodes/build_context.py` | 툴 내부로 흡수 |
| `src/graph/nodes/generate_answer.py` | 에이전트 LLM이 직접 담당 |
| `src/graph/nodes/prepare_context.py` | 불필요 |
| `src/graph/state/chat_state.py` | 불필요 |
| `src/graph/state/rag_state.py` | AgentState로 대체 |
| `src/llm/chains/answer_chain.py` | 에이전트 LLM이 직접 담당 |

---

## 상세 설계

### 1. `src/llm/tools/product_search_tool.py`

기존 RAG 파이프라인 (retrieve → fetch → build_context) 을 툴 함수 하나로 래핑.
LangChain `@tool` 데코레이터로 에이전트가 호출 가능한 함수로 등록.

```python
@tool
def search_products(query: str) -> str:
    """
    Baristation에서 판매하는 커피 원두·제품을 의미 기반으로 검색한다.
    제품 추천, 원두 비교, 특정 맛/원산지 탐색 시 사용한다.
    반환값에는 product_id, 제품명, 원산지, 로스팅, 맛 특성, 플레이버 노트가 포함된다.
    """
    # 1. Qdrant 벡터 검색
    hits = search_qdrant(query, top_k=settings.qdrant_top_k)
    product_ids = [h.payload["product_id"] for h in hits]

    # 2. MySQL 상세 조회
    products = fetch_products_by_ids(product_ids)
    flavors  = fetch_flavors_by_product_ids(product_ids)
    products = enrich_with_flavors(products, flavors)

    # 3. 에이전트가 읽을 수 있는 텍스트로 직렬화
    # product_ids는 JSON 헤더로 포함 → 응답 파싱 시 추출
    return format_products_for_agent(products, hits)
```

툴 docstring이 에이전트에게 "언제 이 툴을 써야 하는지" 알려주는 역할을 한다.

### 2. `src/llm/tools/doc_search_tool.py`

메뉴얼 RAG 추가 전까지는 스텁으로 유지.

```python
@tool
def search_website_docs(query: str) -> str:
    """
    Baristation 웹사이트 이용 방법, 주문, 배송, 회원, 결제 관련 문서를 검색한다.
    사이트 사용법 질문 시 사용한다.
    """
    # TODO: 메뉴얼 Qdrant 컬렉션 구축 후 구현
    return "현재 사이트 이용 안내 검색 기능을 준비 중입니다."
```

### 3. `src/llm/prompts/agent_prompt.py`

에이전트 행동 원칙을 정의. 기존 `chat_prompt.py`의 커피 전문가 역할은 유지하되, 툴 사용 판단 기준 추가.

```
역할: Baristation 커피 전문 AI 어시스턴트
언어: 한국어 (사용자가 다른 언어 요청 시 해당 언어)

툴 사용 원칙:
- 제품 추천·비교·탐색 → search_products 호출
- 사이트 이용·주문·배송 → search_website_docs 호출
- 두 정보가 모두 필요한 질문 → 두 툴 모두 호출 후 통합 답변
- 커피 일반 지식 → 툴 없이 직접 답변

답변 원칙:
- search_products 결과에 있는 제품만 추천 (없는 제품 지어내지 않기)
- 정보가 부족하면 솔직하게 고지
- 추천 이유를 맛 특성(산미/단맛/바디/밸런스), 원산지, 플레이버 노트로 설명
```

### 4. `src/graph/workflows/agent_graph.py`

LangGraph `create_react_agent`로 ReAct 루프 구성.

```python
from langgraph.prebuilt import create_react_agent
from src.llm.tools.product_search_tool import search_products
from src.llm.tools.doc_search_tool import search_website_docs

class AgentGraphWorkflow:
    def __init__(self) -> None:
        model = build_chat_model()
        tools = [search_products, search_website_docs]
        self.app = create_react_agent(
            model=model,
            tools=tools,
            prompt=AGENT_SYSTEM_PROMPT,
        )

    def run(self, question: str) -> dict:
        result = self.app.invoke({"messages": [("user", question)]})
        final_message = result["messages"][-1].content

        # 툴 호출 기록에서 product_ids, sources 추출
        product_ids, sources = extract_metadata_from_messages(result["messages"])

        return {
            "answer": final_message,
            "recommended_product_ids": product_ids,
            "sources": sources,
        }
```

### 5. 메타데이터 추출 (`extract_metadata_from_messages`)

에이전트의 툴 응답 메시지에서 product_id, score 등을 파싱.
툴이 JSON 헤더를 포함한 응답을 반환하는 방식으로 구현:

```
[PRODUCTS]
[{"product_id": 42, "score": 0.91, "name": "..."}]
[/PRODUCTS]

에티오피아 예가체프는 ...
```

`extract_metadata_from_messages()`가 메시지 히스토리에서 `[PRODUCTS]` 블록을 파싱.

### 6. `src/services/chat_service.py` 변경

```python
# Before
self.workflow = ChatGraphWorkflow()
self.rag_workflow = RagGraphWorkflow()
def generate_reply(self, message: str, use_rag: bool = False) -> dict: ...

# After
self.agent = AgentGraphWorkflow()
def generate_reply(self, message: str) -> dict:
    result = self.agent.run(question=message)
    return {
        "answer": result["answer"],
        "workflow": "agent",
        "recommended_product_ids": result["recommended_product_ids"],
        "sources": result["sources"],
    }
```

---

## ReAct 루프 동작 예시

```
질문: "산미 강한 에티오피아 원두 추천해주고, 사이트에서 어떻게 구매하는지도 알려줘"

[Thought] 제품 추천과 구매 방법 두 가지가 필요하다.
[Action]  search_products("산미 강한 에티오피아 원두")
[Result]  예가체프 A (score: 0.93), 시다마 B (score: 0.88), ...

[Thought] 구매 방법은 사이트 문서가 필요하다.
[Action]  search_website_docs("구매 방법")
[Result]  "현재 사이트 이용 안내 검색 기능을 준비 중입니다."

[Final Answer]
산미가 강한 에티오피아 원두로 예가체프 A를 추천드립니다.
산미 8/10, 플레이버는 자스민·레몬·베르가못이 특징입니다.
사이트 구매 안내는 현재 준비 중입니다. (이후 메뉴얼 추가 시 자동으로 응답)
```

---

## 테스트 계획

### `tests/llm/tools/test_product_search_tool.py`

```python
# Qdrant, MySQL을 mock
# search_products("에티오피아")가 올바른 형식의 문자열 반환하는지
# [PRODUCTS] 블록에 product_id가 포함되는지
```

### `tests/graph/test_agent_graph.py`

```python
# AgentGraphWorkflow.run()이 answer, recommended_product_ids, sources를 반환하는지
# 툴 호출 없이 답변 가능한 질문에서 툴 미호출인지 (mock으로 검증)
```

---

## 고려 사항

### Latency

- ReAct 루프는 툴 호출 수만큼 LLM 라운드트립이 발생
- 단순 질문(툴 1회): 기존 RAG와 거의 동일
- 복잡한 질문(툴 2회): 약 1.5~2배 증가
- 허용 가능 범위: 커피 추천 특성상 실시간성보다 정확도가 중요

### 무한 루프 방지

`create_react_agent`의 `recursion_limit` 설정으로 최대 툴 호출 횟수 제한:
```python
self.app = create_react_agent(..., config={"recursion_limit": 10})
```

### 기존 API 호환성

`use_rag` 필드 제거 시 기존 클라이언트가 보내도 Pydantic이 무시 (breaking change 아님).
`workflow` 응답 값이 `"rag-qdrant"` → `"agent"` 로 변경됨 (클라이언트 확인 필요).

---

## 구현 순서

1. `src/llm/prompts/agent_prompt.py` 작성
2. `src/llm/tools/product_search_tool.py` 작성 (기존 노드 로직 이식)
3. `src/llm/tools/doc_search_tool.py` 스텁 작성
4. `src/graph/workflows/agent_graph.py` 작성
5. `tests/llm/tools/test_product_search_tool.py` 작성
6. `tests/graph/test_agent_graph.py` 작성
7. `src/services/chat_service.py` 수정
8. `apps/api/routes/chat.py` 수정 (`use_rag` 제거)
9. 기존 노드/워크플로우/체인 파일 삭제
