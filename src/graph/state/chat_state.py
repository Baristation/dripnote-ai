from typing import TypedDict


class ChatState(TypedDict):
    # LLM-only graph에서 사용할 사용자 질문입니다.
    question: str
    # RAG가 아닌 단순 채팅에서도 외부 context를 붙일 수 있도록 둔 필드입니다.
    context: str
