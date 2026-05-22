from threading import Lock

from src.graph.state.rag_state import RagState
from src.llm.chains.answer_chain import AnswerChain


# 모듈 수준 변수: 이 파일이 import될 때 한 번 생성되고, 이후 모든 요청에서 재사용됩니다.
_chain: AnswerChain | None = None
_chain_lock = Lock()


def _answer_chain() -> AnswerChain:
    # global: 함수 안에서 모듈 수준 변수를 수정할 때 선언합니다. 없으면 새 지역 변수로 인식합니다.
    global _chain
    if _chain is None:
        with _chain_lock:
            # Double-checked locking: lock 획득 후 다른 스레드가 이미 생성했는지 한 번 더 확인합니다.
            if _chain is None:
                _chain = AnswerChain()
    return _chain


def generate_answer(state: RagState) -> RagState:
    chain = _answer_chain()
    answer = chain.invoke(
        question=state["question"],
        # state.get("context", ""): context가 없으면 빈 문자열을 씁니다.
        context=state.get("context", ""),
    )
    return {
        "answer": answer,
    }
