from langgraph.graph import END, START, StateGraph

from src.graph.nodes.build_context import build_context
from src.graph.nodes.fetch_products import fetch_products
from src.graph.nodes.generate_answer import generate_answer
from src.graph.nodes.normalize_query import normalize_query
from src.graph.nodes.retrieve_qdrant import retrieve_qdrant
from src.graph.state.rag_state import RagState


class RagGraphWorkflow:
    def __init__(self) -> None:
        # StateGraph(RagState): RagState를 공유 저장소로 쓰는 그래프를 만듭니다.
        # 각 노드는 state dict를 받아 자기가 담당하는 key만 채운 dict를 반환하고,
        # LangGraph가 반환값을 기존 state에 자동으로 merge합니다.
        graph = StateGraph(RagState)

        # add_node("이름", 함수): 그래프에 처리 단계를 등록합니다.
        graph.add_node("normalize_query", normalize_query)
        graph.add_node("retrieve_qdrant", retrieve_qdrant)
        graph.add_node("fetch_products", fetch_products)
        graph.add_node("build_context", build_context)
        graph.add_node("generate_answer", generate_answer)

        # add_edge(A, B): A가 끝나면 B로 넘어갑니다.
        # START/END는 LangGraph가 제공하는 시작/종료 지점입니다.
        graph.add_edge(START, "normalize_query")
        graph.add_edge("normalize_query", "retrieve_qdrant")
        graph.add_edge("retrieve_qdrant", "fetch_products")
        graph.add_edge("fetch_products", "build_context")
        graph.add_edge("build_context", "generate_answer")
        graph.add_edge("generate_answer", END)

        # compile(): 노드와 엣지 정의를 실행 가능한 그래프로 변환합니다.
        self.app = graph.compile()

    def run(self, question: str) -> RagState:
        # invoke(초기state): 그래프를 실행합니다. 각 노드가 순서대로 state를 채우고 최종 state를 반환합니다.
        return self.app.invoke({"question": question})
