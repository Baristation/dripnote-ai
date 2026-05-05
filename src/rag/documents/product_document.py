def build_product_document(product: dict, flavors: list[dict]) -> str:
    # Qdrant에 넣을 vector text입니다. 검색 품질을 위해 상품/원두/로스터/향미 정보를 한 문서로 합칩니다.
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

    return f"""
Product: {product.get("product_name_ko") or ""} ({product.get("product_name_en") or ""})
Roaster: {product.get("roaster_name_ko") or ""} ({product.get("roaster_name_en") or ""})
Bean: {product.get("bean_name_ko") or ""} ({product.get("bean_name_en") or ""})
Origin: {product.get("origin") or ""}
Region: {product.get("region") or ""}
Process: {product.get("process") or ""}
Variety: {product.get("variety") or ""}
Altitude: {product.get("altitude_min") or ""} - {product.get("altitude_max") or ""}
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
    # payload는 검색 결과 후 MySQL 재조회와 프론트 응답 source 구성에 쓰는 구조화 metadata입니다.
    return {
        "productId": product.get("product_id"),
        "beanId": product.get("bean_id"),
        "roasterId": product.get("roaster_id"),
        "productNameKo": product.get("product_name_ko"),
        "productNameEn": product.get("product_name_en"),
        "roasterNameKo": product.get("roaster_name_ko"),
        "roasterNameEn": product.get("roaster_name_en"),
        "roastLevel": product.get("roasting_level"),
        "origin": product.get("origin"),
        "region": product.get("region"),
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
