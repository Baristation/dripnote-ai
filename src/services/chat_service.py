from src.graph.workflows.chat_graph import ChatGraphWorkflow
from src.llm.chains.answer_chain import AnswerChain
from src.services.retrieval_service import RetrievalService


class ChatService:
    def __init__(self) -> None:
        # LangGraph는 요청 흐름을 제어하고,
        # LangChain 체인은 실제 모델 호출을 담당한다.
        self.workflow = ChatGraphWorkflow()
        self.chain = AnswerChain()
        self.retrieval_service = RetrievalService()

    def generate_reply(self, message: str, use_rag: bool = False) -> dict[str, str]:
        context = ""
        workflow = "llm-only"

        # RAG 옵션이 켜져 있으면 먼저 관련 문맥을 검색한다.
        if use_rag:
            context = self.retrieval_service.retrieve_context(message)
            workflow = "rag"

        # 그래프에서 입력을 정리한 뒤 LLM 체인에 넘긴다.
        graph_result = self.workflow.run(message=message, context=context)
        answer = self.chain.invoke(question=graph_result["question"], context=graph_result["context"])
        return {"answer": answer, "workflow": workflow}
