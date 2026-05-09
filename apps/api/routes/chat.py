from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services.chat_service import ChatService


router = APIRouter(tags=["chat"])
# ChatService 내부 client들은 lazy initialization이라 앱 import/healthcheck 시 외부 API key가 필요 없습니다.
chat_service = ChatService()


class ChatRequest(BaseModel):
    # use_rag=true면 Qdrant + MySQL read-only 기반 LangGraph RAG 경로를 탑니다.
    # false면 외부 검색 없이 LLM-only 답변을 생성합니다.
    message: str = Field(..., min_length=1)
    use_rag: bool = False


class ChatSource(BaseModel):
    # RAG 답변이 어떤 상품을 근거로 했는지 프론트/디버깅에 전달합니다.
    # score는 Qdrant similarity 점수이며, 사용자가 직접 볼 값이라기보다 랭킹 검증용 metadata입니다.
    product_id: int
    product_name: str
    roaster_name: str | None = None
    matched_flavors: list[str] = Field(default_factory=list)
    score: float | None = None


class ChatResponse(BaseModel):
    # answer는 사용자에게 보여줄 자연어 답변입니다.
    answer: str
    # workflow는 어떤 경로(llm-only/rag-qdrant)로 답변이 만들어졌는지 확인하기 위한 값입니다.
    workflow: str
    # 프론트가 상품 카드나 상세 API를 바로 조회할 수 있게 추천 상품 id를 별도로 제공합니다.
    recommended_product_ids: list[int] = Field(default_factory=list)
    # sources는 답변 근거 표시와 디버깅을 위한 상세 source 목록입니다.
    sources: list[ChatSource] = Field(default_factory=list)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    # 백엔드 프록시 또는 프론트가 호출하는 채팅 엔드포인트입니다.
    result = chat_service.generate_reply(message=request.message, use_rag=request.use_rag)
    return ChatResponse(**result)
