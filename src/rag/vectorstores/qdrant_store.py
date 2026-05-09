from functools import lru_cache

from src.core.config import get_settings


_collection_ready = False


@lru_cache(maxsize=1)
def get_qdrant_client():
    # qdrant-client import를 함수 안으로 늦춰 테스트/헬스체크 import 비용을 줄입니다.
    # 또한 Qdrant가 실제로 필요한 코드 경로에서만 외부 의존성이 로딩되어, 단순 API import가 더 가벼워집니다.
    # QdrantClient는 내부 HTTP client를 들고 있으므로 Redis/MySQL client처럼 프로세스 안에서 재사용합니다.
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key or None,
        # 로컬 compose의 Qdrant 서버와 pip로 설치된 client minor version이 다를 수 있습니다.
        # 개발 중에는 warning 때문에 로그가 묻히지 않도록 호환성 경고를 끄고, 실제 호출부에서 API 차이를 흡수합니다.
        check_compatibility=False,
    )


def _reset_collection_ready() -> None:
    # 검색/업서트 중 collection not found가 발생하면 준비 상태 캐시를 풀고 다시 확인하게 합니다.
    global _collection_ready
    _collection_ready = False


def _is_collection_missing_error(error: Exception) -> bool:
    # qdrant-client/server 버전에 따라 collection 없음 예외 타입과 메시지가 조금씩 다를 수 있습니다.
    # 그래서 특정 타입 하나에 묶지 않고 메시지에서 collection missing 계열만 좁게 감지합니다.
    message = str(error).lower()
    return "collection" in message and (
        "not found" in message
        or "doesn't exist" in message
        or "does not exist" in message
    )


def ensure_collection(force: bool = False) -> None:
    # 인덱싱/검색 전에 collection이 없으면 생성합니다.
    # Qdrant collection은 vector size가 한 번 정해지면 기존 point와 호환되어야 하므로 embedding 모델 변경 시 주의가 필요합니다.
    from qdrant_client.http.models import Distance, VectorParams

    global _collection_ready
    if _collection_ready and not force:
        return

    settings = get_settings()
    client = get_qdrant_client()
    collections = client.get_collections().collections
    # get_collections() 결과에는 전체 collection 목록이 들어오므로 이름으로 존재 여부만 확인합니다.
    exists = any(collection.name == settings.qdrant_collection for collection in collections)

    if exists:
        _collection_ready = True
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=settings.qdrant_vector_size,
            # 추천/검색용 embedding은 보통 벡터 방향 유사도를 보는 cosine distance를 사용합니다.
            distance=Distance.COSINE,
        ),
    )
    _collection_ready = True


def upsert_product_vectors(points: list) -> None:
    # product_id를 point id로 쓰기 때문에 같은 상품은 중복 생성 대신 갱신됩니다.
    # 백엔드 상품이 수정된 뒤 재색인하면 같은 id의 vector/payload가 최신 값으로 덮어써집니다.
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()
    try:
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    except Exception as error:
        if not _is_collection_missing_error(error):
            raise
        _reset_collection_ready()
        ensure_collection(force=True)
        client.upsert(collection_name=settings.qdrant_collection, points=points)


def _query_points(client, collection_name: str, query_vector: list[float], limit: int) -> list:
    # 새 qdrant-client에는 query_points()가 있으므로 신규 API를 우선 사용합니다.
    # 구버전 client에서만 search()로 fallback합니다.
    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
            # payload가 있어야 다음 단계에서 productId를 꺼내 MySQL 재조회가 가능합니다.
            with_payload=True,
        )
        return response.points

    return client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit,
        with_payload=True,
    )


def search_products(query_vector: list[float], limit: int | None = None) -> list[dict]:
    # LangGraph retrieve 노드에서 호출하는 semantic search 진입점입니다.
    # 입력은 사용자 질문을 embedding한 vector이고, 출력은 productId payload를 포함한 후보 상품 목록입니다.
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()

    search_limit = limit or settings.qdrant_top_k
    try:
        hits = _query_points(
            client=client,
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=search_limit,
        )
    except Exception as error:
        if not _is_collection_missing_error(error):
            raise
        _reset_collection_ready()
        ensure_collection(force=True)
        hits = _query_points(
            client=client,
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=search_limit,
        )

    return [
        {
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload or {},
        }
        for hit in hits
    ]
