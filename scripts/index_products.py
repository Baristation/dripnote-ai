from src.rag.pipelines.product_index_pipeline import ProductIndexPipeline


def main() -> None:
    # 배치/수동 실행용 상품 인덱싱 CLI입니다.
    count = ProductIndexPipeline().run()
    print(f"indexed {count} products")


if __name__ == "__main__":
    main()
