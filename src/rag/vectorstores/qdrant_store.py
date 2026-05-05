from src.core.config import get_settings


def get_qdrant_client():
    # qdrant-client import를 함수 안으로 늦춰 테스트/헬스체크 import 비용을 줄입니다.
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
    )


def ensure_collection() -> None:
    # 인덱싱/검색 전에 collection이 없으면 생성합니다. vector size는 embedding 모델과 맞아야 합니다.
    from qdrant_client.http.models import Distance, VectorParams

    settings = get_settings()
    client = get_qdrant_client()
    collections = client.get_collections().collections
    exists = any(collection.name == settings.qdrant_collection for collection in collections)

    if exists:
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=settings.qdrant_vector_size,
            distance=Distance.COSINE,
        ),
    )


def upsert_product_vectors(points: list) -> None:
    # product_id를 point id로 쓰기 때문에 같은 상품은 중복 생성 대신 갱신됩니다.
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()
    client.upsert(collection_name=settings.qdrant_collection, points=points)


def search_products(query_vector: list[float], limit: int | None = None) -> list[dict]:
    # LangGraph retrieve 노드에서 호출하는 semantic search 진입점입니다.
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()
    hits = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=limit or settings.qdrant_top_k,
        with_payload=True,
    )
    return [
        {
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload or {},
        }
        for hit in hits
    ]
