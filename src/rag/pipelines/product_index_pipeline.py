from typing import TypeVar

from src.core.config import get_settings
from src.db.repositories.product_read_repository import (
    fetch_flavors_by_product_ids,
    fetch_products_for_indexing,
)
from src.llm.clients.openai_client import build_embeddings
from src.rag.documents.product_document import build_product_document, build_product_payload
from src.rag.vectorstores.qdrant_store import upsert_product_vectors


T = TypeVar("T")


def _chunked(items: list[T], size: int) -> list[list[T]]:
    # OpenAI TPM 제한을 넘지 않도록 상품 문서를 작은 묶음으로 나눕니다.
    # size가 0 이하로 들어오면 무한 루프가 될 수 있어 최소 1로 보정합니다.
    chunk_size = max(size, 1)
    return [items[index : index + chunk_size] for index in range(0, len(items), chunk_size)]


def _embed_documents_with_retry(embeddings, documents: list[str]) -> list[list[float]]:
    # OpenAI의 RPM/TPM 제한은 짧은 시간 뒤 회복될 수 있으므로 제한 에러에 한해 재시도합니다.
    # import를 함수 안에 두어 테스트/healthcheck 경로에서 OpenAI 패키지 세부 타입 로딩을 늦춥니다.
    from openai import RateLimitError
    from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

    @retry(
        retry=retry_if_exception_type(RateLimitError),
        wait=wait_exponential(multiplier=2, min=2, max=60),
        stop=stop_after_attempt(6),
        reraise=True,
    )
    def _embed() -> list[list[float]]:
        return embeddings.embed_documents(documents)

    return _embed()


class ProductIndexPipeline:
    def run(self) -> int:
        # qdrant-client 타입 import는 실제 인덱싱 시점에만 필요합니다.
        # API 서버가 뜰 때마다 Qdrant 타입을 미리 로딩하지 않아도 되므로 healthcheck/import 비용이 줄어듭니다.
        from qdrant_client.http.models import PointStruct

        settings = get_settings()

        # AI 서버는 백엔드 MySQL 8005 포트에 read-only로 접근해 상품 데이터를 읽습니다.
        products = fetch_products_for_indexing()
        product_ids = [int(product["product_id"]) for product in products]

        # 향미는 N:M 관계라 상품 기본 조회와 분리해서 한 번에 가져온 뒤 product_id로 묶습니다.
        # 이렇게 하면 상품 개수만큼 향미 조회가 반복되는 N+1 쿼리 문제를 피할 수 있습니다.
        flavors_by_product_id = fetch_flavors_by_product_ids(product_ids)

        # embedding client는 OpenAI API key와 모델명을 설정에서 읽습니다.
        # 현재 기본 vector size는 text-embedding-3-small의 1536차원을 기준으로 합니다.
        embeddings = build_embeddings()

        documents: list[str] = []
        payloads: list[dict] = []
        point_ids: list[int] = []

        for product in products:
            product_id = int(product["product_id"])
            flavors = flavors_by_product_id.get(product_id, [])

            # LLM/RAG 검색에 잘 걸리도록 사람이 읽는 문장 형태로 document를 구성합니다.
            document = build_product_document(product, flavors)
            documents.append(document)
            payloads.append(build_product_payload(product, flavors, document))
            point_ids.append(product_id)

        if not documents:
            return 0

        # 상품마다 embed_query를 호출하면 OpenAI RPM 제한에 쉽게 걸립니다.
        # 그렇다고 전체 documents를 한 번에 보내면 TPM 제한을 넘을 수 있으므로 작은 batch로 나눠 보냅니다.
        vectors: list[list[float]] = []
        for document_batch in _chunked(documents, settings.embedding_batch_size):
            vectors.extend(_embed_documents_with_retry(embeddings, document_batch))

        points: list[PointStruct] = []
        for point_id, vector, payload in zip(point_ids, vectors, payloads, strict=True):
            # Qdrant point id는 product_id로 고정해 재색인 시 upsert가 되도록 합니다.
            points.append(
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            )

        upsert_product_vectors(points)
        return len(points)
