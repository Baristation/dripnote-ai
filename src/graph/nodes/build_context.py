from src.graph.state.rag_state import RagState
from src.rag.documents.product_document import build_product_document


def build_context(state: RagState) -> RagState:
    products = state.get("products", [])
    qdrant_hits = state.get("qdrant_hits", [])

    # dict 컴프리헨션: {key: value for 변수 in 반복가능객체 if 조건} 형태로 dict를 한 줄에 만듭니다.
    # Qdrant score를 product_id로 빠르게 찾기 위한 lookup table입니다.
    score_by_product_id = {
        int(hit["payload"]["productId"]): hit.get("score")
        for hit in qdrant_hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    }

    context_parts: list[str] = []
    sources: list[dict] = []

    # sorted(반복가능객체, key=정렬기준함수, reverse=True): 내림차순 정렬입니다.
    # lambda product: ...: 익명 함수. 각 product를 받아 score를 반환합니다. 이 score 기준으로 정렬합니다.
    # or 0.0: score가 None이면 0.0으로 대체합니다. None끼리 비교하면 오류가 나므로 숫자로 통일합니다.
    products_sorted = sorted(
        products,
        key=lambda product: score_by_product_id.get(int(product["product_id"]), 0.0) or 0.0,
        reverse=True,
    )

    for product in products_sorted:
        product_id = int(product["product_id"])
        flavors = product.get("flavors", [])

        context_parts.append(build_product_document(product, flavors))
        sources.append(
            {
                "product_id": product_id,
                "product_name": product.get("product_name_ko") or "",
                "roaster_name": product.get("roaster_name_ko") or "",
                # 리스트 컴프리헨션으로 향미 이름만 추출합니다. name_ko가 없는 항목은 제외합니다.
                "matched_flavors": [
                    flavor.get("name_ko") for flavor in flavors if flavor.get("name_ko")
                ],
                "score": score_by_product_id.get(product_id),
            }
        )

    # "\n\n---\n\n".join(list): list의 각 항목을 구분자로 이어 붙입니다.
    context = "\n\n---\n\n".join(context_parts)
    return {
        "context": context,
        "sources": sources,
        # 리스트 컴프리헨션으로 sources에서 product_id만 추출합니다.
        "recommended_product_ids": [source["product_id"] for source in sources],
    }
