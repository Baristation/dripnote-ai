from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.retrieval_service import RetrievalService


router = APIRouter(tags=["rag"])
retrieval_service = RetrievalService()


class IndexRequest(BaseModel):
    directory: str = Field(..., description="Folder path containing source files to index")


@router.post("/rag/index")
def build_index(request: IndexRequest) -> dict[str, str]:
    location = retrieval_service.index_directory(request.directory)
    return {"status": "indexed", "location": location}
