from src.graph.state.chat_state import ChatState


def prepare_context(state: ChatState) -> ChatState:
    context = state["context"].strip()
    if context:
        context = f"Retrieved context:\n{context}"
    return {"question": state["question"], "context": context}
