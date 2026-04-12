from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.services.chat_service import ChatService


router = APIRouter(tags=["chat"])
chat_service = ChatService()


# 채팅 요청 형식
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    use_rag: bool = False


# 채팅 응답 형식
class ChatResponse(BaseModel):
    answer: str
    workflow: str


# 프론트나 다른 백엔드가 호출하는 채팅 API
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = chat_service.generate_reply(message=request.message, use_rag=request.use_rag)
    return ChatResponse(**result)
