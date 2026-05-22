from src.db.repositories.product_read_repository import (
    fetch_flavors_by_product_ids,
    fetch_products_by_ids,
)
from src.graph.state.rag_state import RagState


def fetch_products(state: RagState) -> RagState:
    # state.get("key", 기본값): key가 없으면 기본값을 반환합니다.
    product_ids = state.get("product_ids", [])
    products = fetch_products_by_ids(product_ids)
    # flavors_by_product_id: {product_id: [flavor, ...]} 형태의 dict입니다. product_id로 O(1) 조회가 가능합니다.
    flavors_by_product_id = fetch_flavors_by_product_ids(product_ids)

    enriched_products = []
    for product in products:
        product_id = int(product["product_id"])

        enriched_products.append(
            {
                # **product: product dict의 모든 key-value를 새 dict에 펼쳐 넣습니다. (스프레드 연산자)
                **product,
                # 향미 목록을 상품 dict 안에 붙여 context builder가 한 번에 사용할 수 있게 합니다.
                # dict.get(key, 기본값): key가 없으면 []를 반환합니다.
                "flavors": flavors_by_product_id.get(product_id, []),
            }
        )

    return {
        "products": enriched_products,
    }
