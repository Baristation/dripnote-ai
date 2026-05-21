from src.db.repositories.product_read_repository import (
    fetch_flavors_by_product_ids,
    fetch_products_by_ids,
)
from src.graph.state.rag_state import RagState


def fetch_products(state: RagState) -> RagState:
    # Qdrant payload는 검색용 metadata이므로, 답변 생성 전 MySQL에서 최신 상품 정보를 보강합니다.
    # 이 구조를 유지하면 Qdrant에 오래된 payload가 남아 있어도 답변에는 백엔드 DB의 최신 값이 반영됩니다.
    product_ids = state.get("product_ids", [])
    products = fetch_products_by_ids(product_ids)
    flavors_by_product_id = fetch_flavors_by_product_ids(product_ids)

    enriched_products = []
    for product in products:
        product_id = int(product["product_id"])

        # 향미 목록을 상품 dict 안에 붙여 context builder가 한 번에 사용할 수 있게 합니다.
        # repository는 DB row를 평평한 dict로 반환하고, graph node에서 RAG용 구조로 한 번 더 정리합니다.
        enriched_products.append(
            {
                **product,
                "flavors": flavors_by_product_id.get(product_id, []),
            }
        )

    # LangGraph가 반환 dict를 기존 state에 merge하므로 DB 보강 결과만 반환합니다.
    return {
        "products": enriched_products,
    }
