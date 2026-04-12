from src.rag.pipelines.index_pipeline import IndexPipeline
from src.rag.pipelines.retrieve_pipeline import RetrievePipeline


class RetrievalService:
    def __init__(self) -> None:
        self.index_pipeline = IndexPipeline()
        self.retrieve_pipeline = RetrievePipeline()

    def index_directory(self, directory: str) -> str:
        return self.index_pipeline.run(directory)

    def retrieve_context(self, query: str) -> str:
        return self.retrieve_pipeline.run(query)
