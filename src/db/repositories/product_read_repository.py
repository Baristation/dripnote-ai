from src.db.mysql import get_mysql_engine


# Qdrant 인덱싱과 RAG 상세 보강에 공통으로 쓰는 상품 기본 조회입니다.
# product가 추천의 최종 대상이고, bean/roaster는 추천 근거를 풍부하게 만드는 보조 데이터입니다.
# 여기서는 ORM 모델을 새로 정의하지 않고 raw SQL을 사용합니다.
# 이유는 AI 서버가 백엔드 DB를 "소유"하지 않고 read-only로 읽기만 하므로, 백엔드 JPA 모델과 중복된 영속성 계층을 만들지 않기 위해서입니다.
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


def _build_bean(row: dict) -> dict:
    return {
        "bean_id": row.get("bean_id"),
        "bean_name_ko": row.get("bean_name_ko"),
        "bean_name_en": row.get("bean_name_en"),
        "process": row.get("process"),
        "origin": row.get("origin"),
        "region": row.get("region"),
        "variety": row.get("variety"),
        "altitude_min": row.get("altitude_min"),
        "altitude_max": row.get("altitude_max"),
    }


def merge_product_rows(rows: list[dict]) -> list[dict]:
    # product와 bean은 N:M 관계라 SQL join 결과에서 같은 product_id가 여러 row로 나올 수 있습니다.
    # Qdrant point는 product_id 하나당 하나여야 하므로, 원두 정보는 beans list로 병합합니다.
    products: dict[int, dict] = {}
    for row in rows:
        product_id = int(row["product_id"])
        product = products.get(product_id)
        if product is None:
            product = {
                **row,
                "beans": [],
            }
            products[product_id] = product

        bean = _build_bean(row)
        if bean["bean_id"] is not None and bean not in product["beans"]:
            product["beans"].append(bean)

    return list(products.values())


def fetch_products_for_indexing() -> list[dict]:
    # 전체 상품을 Qdrant에 재색인할 때 사용합니다.
    # 배치 성격의 함수라 pagination은 아직 두지 않았고, 상품 수가 커지면 LIMIT/OFFSET 또는 updated_at 증분 색인으로 바꾸면 됩니다.
    from sqlalchemy import text

    engine = get_mysql_engine()
    with engine.connect() as connection:
        # mappings()를 사용하면 tuple이 아니라 column alias 기반 dict-like row를 받을 수 있습니다.
        # 뒤 단계에서 product["product_id"]처럼 이름으로 접근하기 위해 이 형태가 편합니다.
        rows = connection.execute(text(PRODUCT_BASE_QUERY)).mappings().all()
    return merge_product_rows([dict(row) for row in rows])


def fetch_products_by_ids(product_ids: list[int]) -> list[dict]:
    # RAG 검색 결과 product_id를 MySQL 최신 데이터로 보강합니다.
    # Qdrant payload에도 일부 metadata가 있지만, 상품명/로스터/원두 정보는 MySQL을 source of truth로 다시 읽습니다.
    if not product_ids:
        return []

    from sqlalchemy import bindparam, text

    # SQLAlchemy text query에서 IN (:ids)를 안전하게 확장하려면 expanding=True가 필요합니다.
    # 직접 문자열 join으로 id를 붙이면 SQL injection과 타입 처리 문제가 생길 수 있습니다.
    query = text(PRODUCT_BY_IDS_QUERY).bindparams(bindparam("product_ids", expanding=True))
    engine = get_mysql_engine()
    with engine.connect() as connection:
        rows = connection.execute(query, {"product_ids": product_ids}).mappings().all()
    return merge_product_rows([dict(row) for row in rows])


def fetch_flavors_by_product_ids(product_ids: list[int]) -> dict[int, list[dict]]:
    # 여러 상품의 향미를 한 번에 조회해 N+1 쿼리를 피합니다.
    # 반환값은 {product_id: [flavor, ...]} 형태라 pipeline/node에서 상품 dict에 쉽게 붙일 수 있습니다.
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
        # 같은 product_id가 여러 flavor_note를 가질 수 있으므로 list에 누적합니다.
        result.setdefault(product_id, []).append(dict(row))
    return result
