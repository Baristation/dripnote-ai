from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services.chat_service import ChatService


router = APIRouter(tags=["chat"])
# ChatService 내부 client들은 lazy initialization이라 앱 import/healthcheck 시 외부 API key가 필요 없습니다.
chat_service = ChatService()


class ChatRequest(BaseModel):
    # use_rag=true면 Qdrant + MySQL read-only 기반 LangGraph RAG 경로를 탑니다.
    message: str = Field(..., min_length=1)
    use_rag: bool = False


class ChatSource(BaseModel):
    # RAG 답변이 어떤 상품을 근거로 했는지 프론트/디버깅에 전달합니다.
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
    # 백엔드 프록시 또는 프론트가 호출하는 채팅 엔드포인트입니다.
    result = chat_service.generate_reply(message=request.message, use_rag=request.use_rag)
    return ChatResponse(**result)
