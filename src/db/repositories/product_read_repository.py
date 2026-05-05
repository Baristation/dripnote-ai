from src.db.mysql import get_mysql_engine


# Qdrant 인덱싱과 RAG 상세 보강에 공통으로 쓰는 상품 기본 조회입니다.
# product가 추천 기준이고, bean/roaster는 추천 근거를 보강하는 데이터입니다.
PRODUCT_BASE_QUERY = """
SELECT
    p.product_id,
    p.name_ko AS product_name_ko,
    p.name_en AS product_name_en,
    p.roasting_level,
    p.agtron_min,
    p.agtron_max,
    p.acidity,
    p.sweetness,
    p.body,
    p.balance,
    p.description AS product_description,
    p.product_url,
    p.created_at,
    p.updated_at,
    r.roaster_id,
    r.name_ko AS roaster_name_ko,
    r.name_en AS roaster_name_en,
    b.bean_id,
    b.name_ko AS bean_name_ko,
    b.name_en AS bean_name_en,
    b.process,
    b.origin,
    b.region,
    b.variety,
    b.altitude_min,
    b.altitude_max
FROM product p
JOIN roasters r ON r.roaster_id = p.roaster_id
JOIN bean_product bp ON bp.product_id = p.product_id
JOIN bean b ON b.bean_id = bp.bean_id
"""

# Qdrant 검색 결과의 product_id 목록으로 최신 MySQL 데이터를 다시 읽을 때 사용합니다.
PRODUCT_BY_IDS_QUERY = PRODUCT_BASE_QUERY + "\nWHERE p.product_id IN :product_ids"

# 향미는 product_flavor_note를 거치는 N:M 관계라 별도 조회 후 product_id 기준으로 합칩니다.
PRODUCT_FLAVORS_QUERY = """
SELECT
    pfn.product_id,
    fn.flavor_note_id,
    fn.flavor_category,
    fn.name_ko,
    fn.name_en
FROM product_flavor_note pfn
JOIN flavor_note fn ON fn.flavor_note_id = pfn.flavor_note_id
WHERE pfn.product_id IN :product_ids
"""


def fetch_products_for_indexing() -> list[dict]:
    # 전체 상품을 Qdrant에 재색인할 때 사용합니다.
    from sqlalchemy import text

    engine = get_mysql_engine()
    with engine.connect() as connection:
        rows = connection.execute(text(PRODUCT_BASE_QUERY)).mappings().all()
    return [dict(row) for row in rows]


def fetch_products_by_ids(product_ids: list[int]) -> list[dict]:
    # RAG 검색 결과 product_id를 MySQL 최신 데이터로 보강합니다.
    if not product_ids:
        return []

    from sqlalchemy import bindparam, text

    query = text(PRODUCT_BY_IDS_QUERY).bindparams(bindparam("product_ids", expanding=True))
    engine = get_mysql_engine()
    with engine.connect() as connection:
        rows = connection.execute(query, {"product_ids": product_ids}).mappings().all()
    return [dict(row) for row in rows]


def fetch_flavors_by_product_ids(product_ids: list[int]) -> dict[int, list[dict]]:
    # 여러 상품의 향미를 한 번에 조회해 N+1 쿼리를 피합니다.
    if not product_ids:
        return {}

    from sqlalchemy import bindparam, text

    query = text(PRODUCT_FLAVORS_QUERY).bindparams(bindparam("product_ids", expanding=True))
    engine = get_mysql_engine()
    with engine.connect() as connection:
        rows = connection.execute(query, {"product_ids": product_ids}).mappings().all()

    result: dict[int, list[dict]] = {}
    for row in rows:
        product_id = int(row["product_id"])
        result.setdefault(product_id, []).append(dict(row))
    return result
