from threading import Lock

from src.graph.state.rag_state import RagState
from src.llm.chains.answer_chain import AnswerChain


_chain: AnswerChain | None = None
_chain_lock = Lock()


def _answer_chain() -> AnswerChain:
    # RAG 답변 생성용 AnswerChain을 lazy singleton으로 관리합니다.
    # 앱 시작/healthcheck 시점에는 OpenAI client를 만들지 않고, 첫 RAG 답변 생성 시점에만 생성한 뒤 재사용합니다.
    global _chain
    if _chain is None:
        with _chain_lock:
            # 첫 RAG 요청이 동시에 여러 개 들어와도 AnswerChain은 한 번만 생성합니다.
            if _chain is None:
                _chain = AnswerChain()
    return _chain


def generate_answer(state: RagState) -> RagState:
    # 앞 노드에서 조립한 상품 context를 LLM prompt에 넣어 최종 답변을 생성합니다.
    # 이 노드는 외부 LLM API를 호출하므로 OPENAI_API_KEY와 모델 접근 권한이 실제로 필요해지는 지점입니다.
    chain = _answer_chain()
    answer = chain.invoke(
        question=state["question"],
        context=state.get("context", ""),
    )
    # LangGraph가 반환 dict를 기존 state에 merge하므로 최종 답변 필드만 반환합니다.
    return {
        "answer": answer,
    }
