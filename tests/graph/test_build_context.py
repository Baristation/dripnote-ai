from src.graph.nodes.build_context import build_context


def test_build_context_orders_products_by_qdrant_score() -> None:
    state = {
        "products": [
            {"product_id": 1, "product_name_ko": "낮은 점수", "flavors": []},
            {"product_id": 2, "product_name_ko": "높은 점수", "flavors": []},
        ],
        "qdrant_hits": [
            {"payload": {"productId": 1}, "score": 0.2},
            {"payload": {"productId": 2}, "score": 0.9},
        ],
    }

    result = build_context(state)

    assert result["recommended_product_ids"] == [2, 1]
    assert result["context"].find("높은 점수") < result["context"].find("낮은 점수")
