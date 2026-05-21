from src.graph.state.rag_state import RagState
from src.llm.clients.openai_client import build_embeddings
from src.rag.vectorstores.qdrant_store import search_products


def retrieve_qdrant(state: RagState) -> RagState:
    # 사용자 질문을 embedding으로 바꾼 뒤 Qdrant에서 유사한 상품 point를 찾습니다.
    # 인덱싱 때 사용한 embedding_model과 검색 때 사용한 embedding_model은 반드시 같거나 호환되어야 합니다.
    query = state.get("normalized_question") or state["question"]
    embeddings = build_embeddings()
    query_vector = embeddings.embed_query(query)
    hits = search_products(query_vector)

    # 다음 노드가 MySQL에서 최신 상품 정보를 다시 읽을 수 있게 productId만 추출합니다.
    # Qdrant point id도 product_id지만, payload.productId를 기준으로 삼아 응답 구조를 명확히 유지합니다.
    product_ids = [
        int(hit["payload"]["productId"])
        for hit in hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    ]
    # LangGraph가 반환 dict를 기존 state에 merge하므로 검색 노드가 만든 값만 반환합니다.
    return {
        "qdrant_hits": hits,
        "product_ids": product_ids,
    }
