from src.rag.vectorstores.chroma_store import get_vector_store


class RetrievePipeline:
    def run(self, query: str, k: int = 4) -> str:
        # 질문과 유사한 문서를 찾아 LLM에 넣을 문맥 문자열로 만든다.
        store = get_vector_store()
        docs = store.similarity_search(query, k=k)
        return "\n\n".join(doc.page_content for doc in docs)
