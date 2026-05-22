from threading import Lock

from src.graph.workflows.chat_graph import ChatGraphWorkflow
from src.graph.workflows.rag_graph import RagGraphWorkflow
from src.llm.chains.answer_chain import AnswerChain


class ChatService:
    def __init__(self) -> None:
        self.workflow = ChatGraphWorkflow()
        self.rag_workflow = RagGraphWorkflow()

        # AnswerChain | None: AnswerChain 또는 None 타입. 아직 생성 전이면 None입니다.
        # OpenAI client는 API key가 필요하므로 앱 import 시점이 아니라 실제 호출 시점에 만듭니다.
        self.chain: AnswerChain | None = None

        # Lock: 멀티스레드 환경에서 한 번에 하나의 스레드만 특정 구간을 실행하게 막는 장치입니다.
        # 첫 동시 요청들이 동시에 AnswerChain을 만들지 않도록 lazy initialization 구간만 보호합니다.
        self._chain_lock = Lock()

    def _answer_chain(self) -> AnswerChain:
        if self.chain is None:
            # with lock: 이 블록 안은 한 번에 하나의 스레드만 진입합니다.
            with self._chain_lock:
                # Double-checked locking: lock 대기 중 다른 스레드가 이미 생성했을 수 있으므로 한 번 더 확인합니다.
                if self.chain is None:
                    self.chain = AnswerChain()
        return self.chain

    def generate_reply(self, message: str, use_rag: bool = False) -> dict:
        if use_rag:
            # RAG 경로는 검색, DB 보강, context 조립, 답변 생성을 LangGraph가 순서대로 처리합니다.
            rag_result = self.rag_workflow.run(question=message)
            # dict.get(key, default): key가 없으면 default를 반환합니다. KeyError가 나지 않습니다.
            return {
                "answer": rag_result.get("answer", ""),
                "workflow": "rag-qdrant",
                "recommended_product_ids": rag_result.get("recommended_product_ids", []),
                "sources": rag_result.get("sources", []),
            }

        graph_result = self.workflow.run(message=message, context="")
        answer = self._answer_chain().invoke(
            question=graph_result["question"],
            context=graph_result["context"],
        )
        return {
            "answer": answer,
            "workflow": "llm-only",
            "recommended_product_ids": [],
            "sources": [],
        }
