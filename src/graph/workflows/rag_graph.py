from langgraph.graph import END, START, StateGraph

from src.graph.nodes.build_context import build_context
from src.graph.nodes.fetch_products import fetch_products
from src.graph.nodes.generate_answer import generate_answer
from src.graph.nodes.normalize_query import normalize_query
from src.graph.nodes.retrieve_qdrant import retrieve_qdrant
from src.graph.state.rag_state import RagState


class RagGraphWorkflow:
    def __init__(self) -> None:
        # RAG 전체 흐름을 LangGraph로 명시해 단계별 확장/테스트가 쉽도록 합니다.
        # 각 node는 RagState dict를 받아 필요한 값을 추가한 새 state를 반환합니다.
        # 이렇게 쪼개두면 이후 query rewrite, 권한 필터, reranker, fallback 같은 단계를 edge로 쉽게 끼울 수 있습니다.
        graph = StateGraph(RagState)

        # 1. normalize_query: 사용자 질문을 검색하기 쉬운 형태로 정리합니다.
        graph.add_node("normalize_query", normalize_query)
        # 2. retrieve_qdrant: 질문 embedding으로 Qdrant에서 후보 상품을 찾습니다.
        graph.add_node("retrieve_qdrant", retrieve_qdrant)
        # 3. fetch_products: 후보 product_id를 기준으로 MySQL 최신 데이터를 다시 읽습니다.
        graph.add_node("fetch_products", fetch_products)
        # 4. build_context: LLM prompt에 넣을 context와 API source 목록을 만듭니다.
        graph.add_node("build_context", build_context)
        # 5. generate_answer: context 기반으로 최종 답변을 생성합니다.
        graph.add_node("generate_answer", generate_answer)

        # 현재는 단방향 기본 RAG 흐름입니다. 이후 intent 분기나 fallback edge를 추가할 수 있습니다.
        graph.add_edge(START, "normalize_query")
        graph.add_edge("normalize_query", "retrieve_qdrant")
        graph.add_edge("retrieve_qdrant", "fetch_products")
        graph.add_edge("fetch_products", "build_context")
        graph.add_edge("build_context", "generate_answer")
        graph.add_edge("generate_answer", END)

        self.app = graph.compile()

    def run(self, question: str) -> RagState:
        # API/service 계층에서는 question만 넘기면 graph가 나머지 state를 채웁니다.
        # 반환 state에는 answer, recommended_product_ids, sources 등이 포함됩니다.
        return self.app.invoke({"question": question})
