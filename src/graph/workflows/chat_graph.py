from langgraph.graph import START, StateGraph

from src.graph.nodes.prepare_context import prepare_context
from src.graph.state.chat_state import ChatState


class ChatGraphWorkflow:
    def __init__(self) -> None:
        # 간단한 예시 그래프:
        # 시작 -> 문맥 정리 노드 -> 종료
        graph = StateGraph(ChatState)
        graph.add_node("prepare_context", prepare_context)
        graph.add_edge(START, "prepare_context")
        self.app = graph.compile()

    def run(self, message: str, context: str = "") -> ChatState:
        return self.app.invoke({"question": message, "context": context})
