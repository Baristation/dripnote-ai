from src.graph.state.rag_state import RagState


def normalize_query(state: RagState) -> RagState:
    # 검색 품질이 흔들리지 않도록 앞뒤 공백과 중복 공백을 정규화합니다.
    question = state["question"].strip()
    return {
        **state,
        "normalized_question": " ".join(question.split()),
    }
