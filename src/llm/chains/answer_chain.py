from langchain_core.prompts import ChatPromptTemplate

from src.llm.clients.openai_client import build_chat_model
from src.llm.prompts.chat_prompt import SYSTEM_PROMPT


class AnswerChain:
    def __init__(self) -> None:
        # 모델 client 생성은 OpenAI API key가 필요하므로 AnswerChain 인스턴스 생성 시점에 수행됩니다.
        # ChatService에서는 lazy initialization으로 감싸서 healthcheck만 할 때는 OpenAI client를 만들지 않게 했습니다.
        self.model = build_chat_model()

        # 시스템 프롬프트와 사용자 입력을 합쳐서 모델에 전달합니다.
        # context가 비어 있으면 일반 채팅처럼 동작하고, RAG 경로에서는 상품 문서 context가 들어옵니다.
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "Question: {question}\n\nContext:\n{context}"),
            ]
        )

    def invoke(self, question: str, context: str = "") -> str:
        # LangChain의 pipe 문법으로 prompt -> model 순서의 runnable chain을 만듭니다.
        # 호출부는 question/context만 넘기면 되고, 실제 message formatting은 prompt가 처리합니다.
        chain = self.prompt | self.model
        response = chain.invoke({"question": question, "context": context})
        return response.content
