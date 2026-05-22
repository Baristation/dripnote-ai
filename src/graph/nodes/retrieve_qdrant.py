from src.graph.state.rag_state import RagState
from src.llm.clients.openai_client import build_embeddings
from src.rag.vectorstores.qdrant_store import search_products


def retrieve_qdrant(state: RagState) -> RagState:
    # state.get("key") or state["key"]: normalized_question이 있으면 쓰고 없으면 원본 question을 씁니다.
    query = state.get("normalized_question") or state["question"]
    embeddings = build_embeddings()
    # embed_query: 문자열을 숫자 벡터(list[float])로 변환합니다. 이 벡터로 Qdrant에서 유사한 상품을 찾습니다.
    query_vector = embeddings.embed_query(query)
    hits = search_products(query_vector)

    # 리스트 컴프리헨션: [표현식 for 변수 in 반복가능객체 if 조건] 형태로 list를 한 줄에 만듭니다.
    product_ids = [
        int(hit["payload"]["productId"])
        for hit in hits
        # hit.get("payload"): payload key가 없으면 None 반환. and로 연결해 None이면 뒤 조건은 평가하지 않습니다.
        if hit.get("payload") and hit["payload"].get("productId") is not None
    ]
    return {
        "qdrant_hits": hits,
        "product_ids": product_ids,
    }
