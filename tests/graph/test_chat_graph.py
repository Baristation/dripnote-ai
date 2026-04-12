from src.graph.workflows.chat_graph import ChatGraphWorkflow


def test_graph_keeps_question() -> None:
    workflow = ChatGraphWorkflow()
    result = workflow.run("hello", "world")
    assert result["question"] == "hello"
    assert "world" in result["context"]
