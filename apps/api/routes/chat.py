from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.services.chat_service import ChatService


# APIRouter: FastAPI에서 라우터를 모듈별로 분리할 때 씁니다. main.py에서 include_router로 합칩니다.
# tags는 Swagger(/docs)에서 API를 그룹으로 묶어 보여주는 용도입니다.
router = APIRouter(tags=["chat"])
# ChatService 내부 client들은 lazy initialization이라 앱 import/healthcheck 시 외부 API key가 필요 없습니다.
chat_service = ChatService()


# BaseModel: Pydantic 모델. HTTP 요청/응답 body의 타입과 유효성 검사를 자동으로 처리합니다.
class ChatRequest(BaseModel):
    # Field(...): ...은 필수값(required)을 의미합니다. min_length=1로 빈 문자열을 막습니다.
    message: str = Field(..., min_length=1)
    # use_rag=true면 Qdrant + MySQL read-only 기반 LangGraph RAG 경로를 탑니다.
    # false면 외부 검색 없이 LLM-only 답변을 생성합니다.
    use_rag: bool = False


class ChatSource(BaseModel):
    product_id: int
    product_name: str
    # str | None: str 또는 None 둘 다 허용하는 타입입니다. (Python 3.10+ 문법)
    roaster_name: str | None = None
    # Field(default_factory=list): 기본값으로 [] 를 쓸 때 factory를 씁니다.
    # 그냥 default=[] 를 쓰면 모든 인스턴스가 같은 list 객체를 공유하는 버그가 생깁니다.
    matched_flavors: list[str] = Field(default_factory=list)
    score: float | None = None


class ChatResponse(BaseModel):
    answer: str
    # workflow는 어떤 경로(llm-only/rag-qdrant)로 답변이 만들어졌는지 확인하기 위한 값입니다.
    workflow: str
    recommended_product_ids: list[int] = Field(default_factory=list)
    sources: list[ChatSource] = Field(default_factory=list)


# @router.post: POST /chat 요청을 이 함수로 연결합니다.
# response_model: 반환값을 ChatResponse 스키마로 직렬화해 Swagger에도 자동으로 문서화합니다.
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = chat_service.generate_reply(message=request.message, use_rag=request.use_rag)
    # **result: dict를 키워드 인자로 풀어서 전달합니다. ChatResponse(answer=..., workflow=...) 와 동일합니다.
    return ChatResponse(**result)
