from src.rag.documents.product_document import build_product_document, build_product_payload


def test_build_product_document_contains_core_fields() -> None:
    product = {
        "product_id": 1,
        "bean_id": 10,
        "roaster_id": 3,
        "product_name_ko": "테스트 원두",
        "product_name_en": "Test Coffee",
        "roaster_name_ko": "테스트 로스터",
        "bean_name_ko": "에티오피아 테스트",
        "origin": "Ethiopia",
        "region": "Yirgacheffe",
        "process": "Washed",
        "variety": "Heirloom",
        "altitude_min": 1900,
        "altitude_max": 2100,
        "roasting_level": "LIGHT",
        "agtron_min": 90,
        "agtron_max": 95,
        "acidity": 5,
        "sweetness": 4,
        "body": 2,
        "balance": 4,
        "product_description": "꽃향과 산미",
        "product_url": "https://example.com",
        "updated_at": "2026-05-05T00:00:00",
    }
    flavors = [{"name_ko": "자스민", "flavor_category": "FLORAL"}]

    document = build_product_document(product, flavors)
    payload = build_product_payload(product, flavors, document)

    assert "테스트 원두" in document
    assert "Ethiopia" in document
    assert "자스민" in document
    assert payload["productId"] == 1
    assert payload["flavorNotes"] == ["자스민"]
