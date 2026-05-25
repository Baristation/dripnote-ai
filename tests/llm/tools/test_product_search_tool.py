import json
from unittest.mock import MagicMock, patch

from src.llm.tools.product_search_tool import PRODUCTS_META_END, PRODUCTS_META_START, search_products

_FAKE_HITS = [
    {
        "id": 1,
        "score": 0.91,
        "payload": {"productId": 42},
    }
]

_FAKE_PRODUCTS = [
    {
        "product_id": 42,
        "product_name_ko": "예가체프 내추럴",
        "product_name_en": "Yirgacheffe Natural",
        "roaster_name_ko": "블루보틀",
        "roaster_name_en": "Blue Bottle",
        "roasting_level": "Light",
        "acidity": 8,
        "sweetness": 7,
        "body": 5,
        "balance": 7,
        "product_description": "산미가 뚜렷한 에티오피아 내추럴.",
        "product_url": "https://example.com/42",
        "beans": [],
    }
]

_FAKE_FLAVORS = {42: [{"name_ko": "자스민", "flavor_category": "Floral"}]}


@patch("src.llm.tools.product_search_tool.qdrant_search", return_value=_FAKE_HITS)
@patch("src.llm.tools.product_search_tool.fetch_products_by_ids", return_value=_FAKE_PRODUCTS)
@patch("src.llm.tools.product_search_tool.fetch_flavors_by_product_ids", return_value=_FAKE_FLAVORS)
@patch("src.llm.tools.product_search_tool.build_embeddings")
def test_search_products_returns_meta_block(mock_embeddings, _f, _p, _q):
    mock_emb = MagicMock()
    mock_emb.embed_query.return_value = [0.0] * 1536
    mock_embeddings.return_value = mock_emb

    result = search_products.invoke({"query": "산미 강한 원두"})

    assert PRODUCTS_META_START in result
    assert PRODUCTS_META_END in result

    meta_raw = result.split(PRODUCTS_META_START)[1].split(PRODUCTS_META_END)[0].strip()
    meta = json.loads(meta_raw)

    assert len(meta) == 1
    assert meta[0]["product_id"] == 42
    assert meta[0]["product_name"] == "예가체프 내추럴"
    assert meta[0]["score"] == 0.91
    assert "자스민" in meta[0]["matched_flavors"]


@patch("src.llm.tools.product_search_tool.qdrant_search", return_value=[])
@patch("src.llm.tools.product_search_tool.build_embeddings")
def test_search_products_empty_results(mock_embeddings, _q):
    mock_emb = MagicMock()
    mock_emb.embed_query.return_value = [0.0] * 1536
    mock_embeddings.return_value = mock_emb

    result = search_products.invoke({"query": "없는 원두"})

    assert PRODUCTS_META_START not in result
    assert "없습니다" in result
