from src.graph.state.rag_state import RagState


def normalize_query(state: RagState) -> RagState:
    # 검색 품질이 흔들리지 않도록 앞뒤 공백과 중복 공백을 정규화합니다.
    # 지금은 최소 정규화만 하지만, 이후 동의어 치환이나 언어 감지/query rewrite 단계로 확장할 수 있습니다.
    question = state["question"].strip()
    # LangGraph가 반환 dict를 기존 state에 merge하므로 이 노드가 담당하는 필드만 반환합니다.
    return {
        "normalized_question": " ".join(question.split()),
    }
