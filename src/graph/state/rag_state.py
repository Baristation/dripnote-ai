from typing import TypedDict


class RagState(TypedDict, total=False):
    question: str
    normalized_question: str
    qdrant_hits: list[dict]
    product_ids: list[int]
    products: list[dict]
    context: str
    answer: str
    recommended_product_ids: list[int]
    sources: list[dict]
