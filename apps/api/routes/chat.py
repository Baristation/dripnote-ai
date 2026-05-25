from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services.chat_service import ChatService


router = APIRouter(tags=["chat"])
chat_service = ChatService()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class ChatSource(BaseModel):
    product_id: int
    product_name: str
    roaster_name: str | None = None
    matched_flavors: list[str] = Field(default_factory=list)
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    workflow: str
    recommended_product_ids: list[int] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = chat_service.generate_reply(message=request.message)
    return ChatResponse(**result)
