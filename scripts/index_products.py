from src.rag.pipelines.product_index_pipeline import ProductIndexPipeline


def main() -> None:
    # 배치/수동 실행용 상품 인덱싱 CLI입니다.
    # Swagger의 /api/rag/index/products와 같은 pipeline을 사용하므로 로컬 테스트와 운영 배치의 동작을 맞출 수 있습니다.
    count = ProductIndexPipeline().run()
    print(f"indexed {count} products")


if __name__ == "__main__":
    # python scripts/index_products.py 형태로 직접 실행할 때만 main을 호출합니다.
    # import 시점에는 배치가 실행되지 않아 테스트에서 안전하게 모듈을 불러올 수 있습니다.
    main()
