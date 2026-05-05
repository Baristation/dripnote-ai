from fastapi import APIRouter

from src.rag.pipelines.product_index_pipeline import ProductIndexPipeline


router = APIRouter(tags=["rag"])


@router.post("/rag/index/products")
def build_product_index() -> dict[str, int | str]:
    # 백엔드 MySQL read-only 데이터를 읽어 Qdrant 상품 collection을 갱신합니다.
    count = ProductIndexPipeline().run()
    return {"status": "indexed", "count": count}
