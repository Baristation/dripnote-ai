from src.graph.state.rag_state import RagState
from src.rag.documents.product_document import build_product_document


def build_context(state: RagState) -> RagState:
    # LLM에 넘길 context와 API 응답에 포함할 sources를 동시에 만듭니다.
    # context는 모델이 자연어 답변을 만들 때 쓰고, sources는 프론트/디버깅에서 "왜 추천됐는지" 확인할 때 씁니다.
    products = state.get("products", [])
    qdrant_hits = state.get("qdrant_hits", [])

    # Qdrant score는 최종 답변 source에 남겨 디버깅/랭킹 확인에 사용합니다.
    # MySQL 재조회 결과에는 score가 없으므로 productId를 key로 하는 lookup table을 미리 만듭니다.
    score_by_product_id = {
        int(hit["payload"]["productId"]): hit.get("score")
        for hit in qdrant_hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    }

    context_parts: list[str] = []
    sources: list[dict] = []
    # MySQL IN 조회 결과 순서는 Qdrant score 순서를 보장하지 않습니다.
    # LLM이 더 관련도 높은 상품을 먼저 보도록 score 내림차순으로 context를 구성합니다.
    products_sorted = sorted(
        products,
        key=lambda product: score_by_product_id.get(int(product["product_id"]), 0.0) or 0.0,
        reverse=True,
    )

    for product in products_sorted:
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
    # LangGraph가 반환 dict를 기존 state에 merge하므로 context/source 관련 결과만 반환합니다.
    return {
        "context": context,
        "sources": sources,
        # API 응답에서 프론트가 바로 상품 상세 조회/카드 렌더링에 사용할 수 있도록 id 목록도 별도로 제공합니다.
        "recommended_product_ids": [source["product_id"] for source in sources],
    }
