from langchain_core.prompts import ChatPromptTemplate

from src.llm.clients.openai_client import build_chat_model
from src.llm.prompts.chat_prompt import SYSTEM_PROMPT


class AnswerChain:
    def __init__(self) -> None:
        self.model = build_chat_model()
        # 시스템 프롬프트와 사용자 입력을 합쳐서 모델에 전달한다.
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "Question: {question}\n\nContext:\n{context}"),
            ]
        )

    def invoke(self, question: str, context: str = "") -> str:
        chain = self.prompt | self.model
        response = chain.invoke({"question": question, "context": context})
        return response.content
