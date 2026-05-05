from src.db.repositories.product_read_repository import (
    fetch_flavors_by_product_ids,
    fetch_products_for_indexing,
)
from src.llm.clients.openai_client import build_embeddings
from src.rag.documents.product_document import build_product_document, build_product_payload
from src.rag.vectorstores.qdrant_store import upsert_product_vectors


class ProductIndexPipeline:
    def run(self) -> int:
        # qdrant-client 타입 import는 실제 인덱싱 시점에만 필요합니다.
        from qdrant_client.http.models import PointStruct

        # AI 서버는 백엔드 MySQL 8005 포트에 read-only로 접근해 상품 데이터를 읽습니다.
        products = fetch_products_for_indexing()
        product_ids = [int(product["product_id"]) for product in products]
        # 향미는 N:M 관계라 상품 기본 조회와 분리해서 한 번에 가져온 뒤 product_id로 묶습니다.
        flavors_by_product_id = fetch_flavors_by_product_ids(product_ids)
        embeddings = build_embeddings()

        points: list[PointStruct] = []
        for product in products:
            product_id = int(product["product_id"])
            flavors = flavors_by_product_id.get(product_id, [])
            # LLM/RAG 검색에 잘 걸리도록 사람이 읽는 문장 형태로 document를 구성합니다.
            document = build_product_document(product, flavors)
            vector = embeddings.embed_query(document)
            payload = build_product_payload(product, flavors, document)

            # Qdrant point id는 product_id로 고정해 재색인 시 upsert가 되도록 합니다.
            points.append(
                PointStruct(
                    id=product_id,
                    vector=vector,
                    payload=payload,
                )
            )

        if points:
            # 빈 데이터일 때 Qdrant에 불필요한 요청을 보내지 않습니다.
            upsert_product_vectors(points)
        return len(points)
