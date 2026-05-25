import json

from langchain_core.tools import tool

from src.db.repositories.product_read_repository import (
    fetch_flavors_by_product_ids,
    fetch_products_by_ids,
)
from src.llm.clients.openai_client import build_embeddings
from src.rag.documents.product_document import build_product_document
from src.rag.vectorstores.qdrant_store import search_products as qdrant_search

PRODUCTS_META_START = "[PRODUCTS_META]"
PRODUCTS_META_END = "[/PRODUCTS_META]"


@tool
def search_products(query: str) -> str:
    """
    Baristation에서 판매하는 커피 원두·제품을 의미 기반으로 검색한다.
    제품 추천, 원두 비교, 특정 맛/원산지/로스팅/플레이버 탐색 시 사용한다.
    반환값에는 제품명, 원산지, 로스팅 수준, 맛 특성, 플레이버 노트가 포함된다.
    """
    normalized = " ".join(query.strip().split())

    embeddings = build_embeddings()
    query_vector = embeddings.embed_query(normalized)
    hits = qdrant_search(query_vector)

    if not hits:
        return "검색된 제품이 없습니다."

    product_ids = [
        int(hit["payload"]["productId"])
        for hit in hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    ]

    if not product_ids:
        return "검색된 제품이 없습니다."

    products = fetch_products_by_ids(product_ids)
    flavors_by_id = fetch_flavors_by_product_ids(product_ids)

    score_by_id = {
        int(hit["payload"]["productId"]): hit.get("score", 0.0)
        for hit in hits
        if hit.get("payload") and hit["payload"].get("productId") is not None
    }

    products_sorted = sorted(
        products,
        key=lambda p: score_by_id.get(int(p["product_id"]), 0.0),
        reverse=True,
    )

    meta: list[dict] = []
    doc_parts: list[str] = []

    for product in products_sorted:
        product_id = int(product["product_id"])
        flavors = flavors_by_id.get(product_id, [])

        meta.append(
            {
                "product_id": product_id,
                "product_name": product.get("product_name_ko") or "",
                "roaster_name": product.get("roaster_name_ko") or "",
                "matched_flavors": [
                    f.get("name_ko") for f in flavors if f.get("name_ko")
                ],
                "score": score_by_id.get(product_id),
            }
        )
        doc_parts.append(build_product_document(product, flavors))

    meta_json = json.dumps(meta, ensure_ascii=False)
    docs = "\n\n---\n\n".join(doc_parts)

    return f"{PRODUCTS_META_START}\n{meta_json}\n{PRODUCTS_META_END}\n\n{docs}"
