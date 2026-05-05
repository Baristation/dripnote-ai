from src.graph.state.rag_state import RagState
from src.rag.documents.product_document import build_product_document


def build_context(state: RagState) -> RagState:
    # LLM에 넘길 context와 API 응답에 포함할 sources를 동시에 만듭니다.
    products = state.get("products", [])
    qdrant_hits = state.get("qdrant_hits", [])
    # Qdrant score는 최종 답변 source에 남겨 디버깅/랭킹 확인에 사용합니다.
    score_by_product_id = {
        int(hit["payload"]["productId"]): hit.get("score")
        for hit in qdrant_hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    }

    context_parts: list[str] = []
    sources: list[dict] = []

    for product in products:
        product_id = int(product["product_id"])
        flavors = product.get("flavors", [])
        # 각 상품을 독립 문서로 만든 뒤 구분자를 넣어 LLM이 상품별 근거를 구분하게 합니다.
        context_parts.append(build_product_document(product, flavors))
        sources.append(
            {
                "product_id": product_id,
                "product_name": product.get("product_name_ko") or "",
                "roaster_name": product.get("roaster_name_ko") or "",
                "matched_flavors": [
                    flavor.get("name_ko") for flavor in flavors if flavor.get("name_ko")
                ],
                "score": score_by_product_id.get(product_id),
            }
        )

    context = "\n\n---\n\n".join(context_parts)
    return {
        **state,
        "context": context,
        "sources": sources,
        "recommended_product_ids": [source["product_id"] for source in sources],
    }
