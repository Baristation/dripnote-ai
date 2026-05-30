import json
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from src.graph.workflows.agent_graph import AgentGraphWorkflow, extract_metadata_from_messages

_META_ITEM = {"product_id": 42, "product_name": "예가체프 내추럴", "roaster_name": "블루보틀", "matched_flavors": ["자스민"], "score": 0.91}
_TOOL_CONTENT = f"[PRODUCTS_META]\n{json.dumps([_META_ITEM], ensure_ascii=False)}\n[/PRODUCTS_META]\n\nProduct: 예가체프 내추럴"


def test_extract_metadata_from_messages():
    messages = [
        HumanMessage(content="산미 강한 원두 추천해줘"),
        AIMessage(content="", tool_calls=[{"id": "call_1", "name": "search_products", "args": {}}]),
        ToolMessage(content=_TOOL_CONTENT, tool_call_id="call_1"),
        AIMessage(content="예가체프 내추럴을 추천드립니다."),
    ]
    product_ids, sources = extract_metadata_from_messages(messages)

    assert product_ids == [42]
    assert len(sources) == 1
    assert sources[0]["product_name"] == "예가체프 내추럴"
    assert sources[0]["score"] == 0.91


def test_extract_metadata_deduplicates_by_product_id():
    # 같은 product_id가 두 번 검색됐을 때 score가 높은 것을 유지한다.
    low = {**_META_ITEM, "score": 0.70}
    high = {**_META_ITEM, "score": 0.91}

    def _tool_msg(item, call_id):
        content = f"[PRODUCTS_META]\n{json.dumps([item], ensure_ascii=False)}\n[/PRODUCTS_META]\n\nProduct: ..."
        return ToolMessage(content=content, tool_call_id=call_id)

    messages = [_tool_msg(low, "call_1"), _tool_msg(high, "call_2")]
    product_ids, sources = extract_metadata_from_messages(messages)

    assert len(product_ids) == 1
    assert sources[0]["score"] == 0.91


def test_extract_metadata_no_tool_messages():
    messages = [
        HumanMessage(content="드립 커피 방법 알려줘"),
        AIMessage(content="핸드드립은 물 온도 93도에서 ..."),
    ]
    product_ids, sources = extract_metadata_from_messages(messages)

    assert product_ids == []
    assert sources == []


@patch("src.graph.workflows.agent_graph.create_react_agent")
@patch("src.graph.workflows.agent_graph.build_chat_model")
def test_agent_graph_workflow_run_returns_expected_keys(mock_model, mock_create):
    fake_app = MagicMock()
    fake_app.invoke.return_value = {
        "messages": [
            HumanMessage(content="원두 추천"),
            ToolMessage(content=_TOOL_CONTENT, tool_call_id="call_1"),
            AIMessage(content="예가체프 내추럴을 추천드립니다."),
        ]
    }
    mock_create.return_value = fake_app

    workflow = AgentGraphWorkflow()
    result = workflow.run("원두 추천")

    assert "answer" in result
    assert "recommended_product_ids" in result
    assert "sources" in result
    assert result["answer"] == "예가체프 내추럴을 추천드립니다."
    assert result["recommended_product_ids"] == [42]
