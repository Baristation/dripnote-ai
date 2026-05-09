from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.core.config import get_settings


def build_chat_model() -> ChatOpenAI:
    # ChatOpenAI는 최종 자연어 답변을 생성하는 모델 client입니다.
    # temperature=0은 추천/설명 결과를 가능한 일관되게 만들기 위한 설정입니다.
    settings = get_settings()
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)


def build_embeddings() -> OpenAIEmbeddings:
    # OpenAIEmbeddings는 질문과 상품 문서를 같은 vector 공간으로 변환합니다.
    # Qdrant collection의 vector size는 이 embedding 모델의 출력 차원과 맞아야 합니다.
    settings = get_settings()
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
