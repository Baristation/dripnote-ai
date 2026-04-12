from pathlib import Path


def load_text_files(directory: str) -> list[dict[str, str]]:
    base_path = Path(directory)
    documents: list[dict[str, str]] = []

    for path in base_path.rglob("*"):
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}:
            documents.append({"page_content": path.read_text(encoding="utf-8"), "source": str(path)})

    return documents
