from typing import TypedDict


# TypedDict: dict인데 각 key의 타입을 명시할 수 있습니다.
# total=False: 모든 key가 선택적(optional)입니다. 노드마다 state를 점진적으로 채우므로 필수값이 없어야 합니다.
class RagState(TypedDict, total=False):
    # 사용자가 입력한 원본 질문입니다.
    question: str
    # normalize_query 노드가 만든 검색용 질문입니다.
    normalized_question: str
    # Qdrant 검색 결과 원본입니다. score와 payload를 포함합니다.
    qdrant_hits: list[dict]
    # Qdrant payload에서 추출한 상품 id 목록입니다.
    product_ids: list[int]
    # MySQL에서 다시 읽어 온 최신 상품 데이터입니다.
    products: list[dict]
    # LLM prompt에 넣을 RAG context 문자열입니다.
    context: str
    # generate_answer 노드가 만든 최종 답변입니다.
    answer: str
    # API 응답에서 프론트가 사용할 추천 상품 id 목록입니다.
    recommended_product_ids: list[int]
    # 답변 근거로 사용된 상품/점수/향미 정보입니다.
    sources: list[dict]
