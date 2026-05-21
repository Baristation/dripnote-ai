from threading import Lock

from src.graph.workflows.chat_graph import ChatGraphWorkflow
from src.graph.workflows.rag_graph import RagGraphWorkflow
from src.llm.chains.answer_chain import AnswerChain


class ChatService:
    def __init__(self) -> None:
        # use_rag=False일 때 쓰는 기존 단순 채팅 그래프입니다.
        self.workflow = ChatGraphWorkflow()

        # use_rag=True일 때 Qdrant/MySQL 기반 RAG 전체 흐름을 실행합니다.
        self.rag_workflow = RagGraphWorkflow()

        # OpenAI client는 API key가 필요하므로 앱 import 시점이 아니라 실제 호출 시점에 만듭니다.
        # 덕분에 /health, /docs 같은 엔드포인트는 OpenAI 설정이 틀려도 서버 기동 자체를 막지 않습니다.
        self.chain: AnswerChain | None = None
        # 첫 동시 요청들이 동시에 AnswerChain을 만들지 않도록 lazy initialization 구간만 보호합니다.
        self._chain_lock = Lock()

    def _answer_chain(self) -> AnswerChain:
        # 테스트/헬스체크에서 OPENAI_API_KEY 없이 앱을 import할 수 있게 lazy initialization을 사용합니다.
        if self.chain is None:
            with self._chain_lock:
                # lock 대기 중 다른 요청이 이미 생성했을 수 있으므로 한 번 더 확인합니다.
                if self.chain is None:
                    self.chain = AnswerChain()
        return self.chain

    def generate_reply(self, message: str, use_rag: bool = False) -> dict:
        if use_rag:
            # RAG 경로는 검색, DB 보강, context 조립, 답변 생성을 LangGraph가 순서대로 처리합니다.
            # 반환값은 FastAPI response model과 맞추기 위해 dict로 정리합니다.
            rag_result = self.rag_workflow.run(question=message)
            return {
                "answer": rag_result.get("answer", ""),
                "workflow": "rag-qdrant",
                "recommended_product_ids": rag_result.get("recommended_product_ids", []),
                "sources": rag_result.get("sources", []),
            }

        # RAG를 쓰지 않는 요청은 기존 LLM-only 경로로 처리합니다.
        # 현재 ChatGraphWorkflow는 질문/context 정리만 담당하고, 실제 답변 생성은 AnswerChain이 수행합니다.
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
