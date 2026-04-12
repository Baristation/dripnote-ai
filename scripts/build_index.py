import argparse

from src.services.retrieval_service import RetrievalService


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local vector index from text files.")
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()

    service = RetrievalService()
    location = service.index_directory(args.directory)
    print(f"index stored in {location}")


if __name__ == "__main__":
    main()
