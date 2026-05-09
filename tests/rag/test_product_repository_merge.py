from src.db.repositories.product_read_repository import merge_product_rows


def test_merge_product_rows_groups_beans_by_product_id() -> None:
    rows = [
        {
            "product_id": 1,
            "product_name_ko": "블렌드",
            "bean_id": 10,
            "bean_name_ko": "원두 A",
            "origin": "Ethiopia",
        },
        {
            "product_id": 1,
            "product_name_ko": "블렌드",
            "bean_id": 11,
            "bean_name_ko": "원두 B",
            "origin": "Kenya",
        },
    ]

    products = merge_product_rows(rows)

    assert len(products) == 1
    assert products[0]["product_id"] == 1
    assert [bean["bean_id"] for bean in products[0]["beans"]] == [10, 11]
