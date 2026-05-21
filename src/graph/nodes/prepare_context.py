from src.graph.state.chat_state import ChatState


def prepare_context(state: ChatState) -> ChatState:
    # LLM-only chat graph에서 context 문자열을 prompt에 넣기 좋은 형태로 정리합니다.
    # RAG 경로에서는 build_context 노드가 별도 context를 만들기 때문에 이 노드는 기존 단순 채팅용입니다.
    context = state["context"].strip()
    if context:
        # context가 있을 때만 라벨을 붙여 모델이 질문과 참고자료를 구분하도록 합니다.
        context = f"Retrieved context:\n{context}"
    return {"question": state["question"], "context": context}
