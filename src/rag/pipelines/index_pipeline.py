from src.rag.loaders.file_loader import load_text_files
from src.rag.vectorstores.chroma_store import upsert_documents


class IndexPipeline:
    def run(self, directory: str) -> str:
        # 폴더 안의 문서를 읽어서 벡터 저장소에 적재한다.
        documents = load_text_files(directory)
        return upsert_documents(documents)
