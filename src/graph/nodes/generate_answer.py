from src.graph.state.rag_state import RagState
from src.llm.chains.answer_chain import AnswerChain


def generate_answer(state: RagState) -> RagState:
    # 앞 노드에서 조립한 상품 context를 LLM prompt에 넣어 최종 답변을 생성합니다.
    chain = AnswerChain()
    answer = chain.invoke(
        question=state["question"],
        context=state.get("context", ""),
    )
    return {
        **state,
        "answer": answer,
    }
