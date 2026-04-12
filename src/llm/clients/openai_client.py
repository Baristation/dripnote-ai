from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.core.config import get_settings


def build_chat_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(model=settings.openai_model, api_key=settings.openai_api_key, temperature=0)


def build_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()
    return OpenAIEmbeddings(model=settings.embedding_model, api_key=settings.openai_api_key)
