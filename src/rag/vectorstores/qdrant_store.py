from functools import lru_cache

from src.core.config import get_settings


_collection_ready = False


# @lru_cache(maxsize=1): 함수를 처음 호출할 때만 실행하고 결과를 캐시합니다.
# maxsize=1: 캐시를 1개만 유지합니다. 같은 인자로 다시 호출하면 캐시된 결과를 반환합니다.
# QdrantClient는 HTTP 연결을 내부에 들고 있으므로 매 요청마다 새로 만들지 않고 재사용합니다.
@lru_cache(maxsize=1)
def get_qdrant_client():
    from qdrant_client import QdrantClient

    settings = get_settings()
    return QdrantClient(
        url=settings.qdrant_url,
        # or None: qdrant_api_key가 빈 문자열("")이면 None으로 바꿉니다. 빈 문자열을 key로 보내면 오류가 납니다.
        api_key=settings.qdrant_api_key or None,
        check_compatibility=False,
    )


def _reset_collection_ready() -> None:
    # global: 모듈 수준 변수를 함수 안에서 수정할 때 선언합니다.
    global _collection_ready
    _collection_ready = False


def _is_collection_missing_error(error: Exception) -> bool:
    # str(error).lower(): 예외 메시지를 소문자로 변환해 대소문자 구분 없이 비교합니다.
    message = str(error).lower()
    # in 연산자: 문자열이 포함되어 있으면 True입니다.
    return "collection" in message and (
        "not found" in message
        or "doesn't exist" in message
        or "does not exist" in message
    )


def ensure_collection(force: bool = False) -> None:
    from qdrant_client.http.models import Distance, VectorParams

    global _collection_ready
    # 이미 준비됐고 강제 재확인이 아니면 바로 반환합니다.
    if _collection_ready and not force:
        return

    settings = get_settings()
    client = get_qdrant_client()
    collections = client.get_collections().collections
    # any(조건): 하나라도 True면 True를 반환합니다. 전체를 순회할 필요 없이 첫 True에서 멈춥니다.
    exists = any(collection.name == settings.qdrant_collection for collection in collections)

    if exists:
        _collection_ready = True
        return

    client.create_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=settings.qdrant_vector_size,
            # Distance.COSINE: 벡터 방향 유사도. 추천/검색용 embedding에 일반적으로 사용합니다.
            distance=Distance.COSINE,
        ),
    )
    _collection_ready = True


def upsert_product_vectors(points: list) -> None:
    # upsert: insert + update. 같은 id가 있으면 덮어쓰고 없으면 새로 만듭니다.
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()
    try:
        client.upsert(collection_name=settings.qdrant_collection, points=points)
    except Exception as error:
        # collection이 없는 에러일 때만 재생성 후 재시도합니다. 다른 에러는 그대로 올립니다.
        if not _is_collection_missing_error(error):
            raise
        _reset_collection_ready()
        ensure_collection(force=True)
        client.upsert(collection_name=settings.qdrant_collection, points=points)


def _query_points(client, collection_name: str, query_vector: list[float], limit: int) -> list:
    # hasattr(객체, "속성명"): 객체에 해당 속성/메서드가 있으면 True입니다. 버전별 API 차이를 흡수할 때 씁니다.
    if hasattr(client, "query_points"):
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit,
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
    settings = get_settings()
    client = get_qdrant_client()
    ensure_collection()

    # limit or settings.qdrant_top_k: limit이 None 또는 0이면 설정값을 씁니다.
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

    # 리스트 컴프리헨션으로 qdrant-client 객체를 dict로 변환합니다.
    # hit.payload or {}: payload가 None이면 빈 dict를 씁니다.
    return [
        {
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload or {},
        }
        for hit in hits
    ]
