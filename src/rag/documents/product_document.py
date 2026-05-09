def _format_bean(bean: dict) -> str:
    return (
        f"{bean.get('bean_name_ko') or ''} ({bean.get('bean_name_en') or ''}), "
        f"origin={bean.get('origin') or ''}, "
        f"region={bean.get('region') or ''}, "
        f"process={bean.get('process') or ''}, "
        f"variety={bean.get('variety') or ''}, "
        f"altitude={bean.get('altitude_min') or ''}-{bean.get('altitude_max') or ''}"
    )


def build_product_document(product: dict, flavors: list[dict]) -> str:
    # Qdrant에 넣을 vector text입니다.
    # embedding 모델은 dict 구조 자체를 이해하는 것이 아니라 "문장/텍스트"를 vector로 바꾸기 때문에,
    # 상품/원두/로스터/향미 정보를 사람이 읽을 수 있는 라벨 달린 텍스트로 합쳐 검색 품질을 높입니다.
    flavor_names = ", ".join(str(flavor.get("name_ko") or "") for flavor in flavors)
    flavor_categories = ", ".join(
        sorted(
            {
                str(flavor.get("flavor_category"))
                for flavor in flavors
                if flavor.get("flavor_category")
            }
        )
    )
    beans = product.get("beans") or [
        {
            "bean_name_ko": product.get("bean_name_ko"),
            "bean_name_en": product.get("bean_name_en"),
            "origin": product.get("origin"),
            "region": product.get("region"),
            "process": product.get("process"),
            "variety": product.get("variety"),
            "altitude_min": product.get("altitude_min"),
            "altitude_max": product.get("altitude_max"),
        }
    ]
    bean_lines = "\n".join(f"- {_format_bean(bean)}" for bean in beans)

    # 영어/한국어 이름을 모두 넣는 이유는 사용자가 "Ethiopia", "에티오피아"처럼 섞어 검색해도 걸리게 하기 위해서입니다.
    # 수치형 특성(acidity/body 등)도 텍스트에 포함해 "산미 있는 원두" 같은 질문에 반응할 여지를 둡니다.
    return f"""
Product: {product.get("product_name_ko") or ""} ({product.get("product_name_en") or ""})
Roaster: {product.get("roaster_name_ko") or ""} ({product.get("roaster_name_en") or ""})
Beans:
{bean_lines}
Roast level: {product.get("roasting_level") or ""}
Agtron: {product.get("agtron_min") or ""} - {product.get("agtron_max") or ""}
Acidity: {product.get("acidity") or ""}
Sweetness: {product.get("sweetness") or ""}
Body: {product.get("body") or ""}
Balance: {product.get("balance") or ""}
Flavor categories: {flavor_categories}
Flavor notes: {flavor_names}
Description: {product.get("product_description") or ""}
Product URL: {product.get("product_url") or ""}
""".strip()


def build_product_payload(product: dict, flavors: list[dict], document: str) -> dict:
    # payload는 vector 검색 결과와 함께 돌아오는 구조화 metadata입니다.
    # 답변 생성 전에는 productId로 MySQL을 다시 조회하고, API 응답에는 source/debug 정보로 일부 payload를 사용할 수 있습니다.
    # document도 payload에 남겨두면 Qdrant 콘솔에서 어떤 텍스트가 색인됐는지 추적하기 쉽습니다.
    beans = product.get("beans") or []
    return {
        "productId": product.get("product_id"),
        "beanId": product.get("bean_id"),
        "beanIds": [bean.get("bean_id") for bean in beans if bean.get("bean_id") is not None],
        "roasterId": product.get("roaster_id"),
        "productNameKo": product.get("product_name_ko"),
        "productNameEn": product.get("product_name_en"),
        "roasterNameKo": product.get("roaster_name_ko"),
        "roasterNameEn": product.get("roaster_name_en"),
        "roastLevel": product.get("roasting_level"),
        "origin": product.get("origin"),
        "region": product.get("region"),
        "beans": beans,
        "flavorCategories": list(
            sorted(
                {
                    str(flavor.get("flavor_category"))
                    for flavor in flavors
                    if flavor.get("flavor_category")
                }
            )
        ),
        "flavorNotes": [flavor.get("name_ko") for flavor in flavors if flavor.get("name_ko")],
        "updatedAt": str(product.get("updated_at")),
        "document": document,
    }
