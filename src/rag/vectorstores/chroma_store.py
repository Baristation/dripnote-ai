from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from src.core.config import get_settings
from src.llm.clients.openai_client import build_embeddings


def get_vector_store() -> Chroma:
    settings = get_settings()
    path = Path(settings.vectorstore_dir)
    path.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name="dripnote-ai",
        persist_directory=str(path),
        embedding_function=build_embeddings(),
    )


def upsert_documents(documents: list[dict[str, str]]) -> str:
    store = get_vector_store()
    langchain_docs = [
        Document(page_content=doc["page_content"], metadata={"source": doc["source"]}) for doc in documents
    ]
    if langchain_docs:
        store.add_documents(langchain_docs)
    return str(store._persist_directory)
