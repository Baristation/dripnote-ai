from src.graph.state.rag_state import RagState
from src.llm.clients.openai_client import build_embeddings
from src.rag.vectorstores.qdrant_store import search_products


def retrieve_qdrant(state: RagState) -> RagState:
    # 사용자 질문을 embedding으로 바꾼 뒤 Qdrant에서 유사한 상품 point를 찾습니다.
    query = state.get("normalized_question") or state["question"]
    embeddings = build_embeddings()
    query_vector = embeddings.embed_query(query)
    hits = search_products(query_vector)
    # 다음 노드가 MySQL에서 최신 상품 정보를 다시 읽을 수 있게 productId만 추출합니다.
    product_ids = [
        int(hit["payload"]["productId"])
        for hit in hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    ]
    return {
        **state,
        "qdrant_hits": hits,
        "product_ids": product_ids,
    }
