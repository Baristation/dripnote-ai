from src.graph.workflows.agent_graph import AgentGraphWorkflow


class ChatService:
    def __init__(self) -> None:
        # AgentGraphWorkflow 자체가 lazy initialization이라 여기서는 외부 API 호출이 없다.
        self.agent = AgentGraphWorkflow()

    def generate_reply(self, message: str) -> dict:
        result = self.agent.run(question=message)
        return {
            "answer": result["answer"],
            "workflow": "agent",
            "recommended_product_ids": result["recommended_product_ids"],
            "sources": result["sources"],
        }
