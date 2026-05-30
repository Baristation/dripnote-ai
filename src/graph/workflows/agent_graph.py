import json
import re
from threading import Lock

from langgraph.prebuilt import create_react_agent

from src.llm.clients.openai_client import build_chat_model
from src.llm.prompts.agent_prompt import AGENT_SYSTEM_PROMPT
from src.llm.tools.doc_search_tool import search_website_docs
from src.llm.tools.product_search_tool import search_products

_META_PATTERN = re.compile(
    r"\[PRODUCTS_META\]\n(.*?)\n\[/PRODUCTS_META\]",
    re.DOTALL,
)


def extract_metadata_from_messages(messages: list) -> tuple[list[int], list[dict]]:
    from langchain_core.messages import ToolMessage

    all_meta: list[dict] = []
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        content = message.content if isinstance(message.content, str) else ""
        match = _META_PATTERN.search(content)
        if not match:
            continue
        try:
            items = json.loads(match.group(1))
            all_meta.extend(items)
        except (json.JSONDecodeError, ValueError):
            pass

    # product_id 중복 제거, 동일 상품이 여러 번 검색됐을 때 score가 높은 것을 유지한다.
    seen: dict[int, dict] = {}
    for item in all_meta:
        pid = item["product_id"]
        if pid not in seen or (item.get("score") or 0) > (seen[pid].get("score") or 0):
            seen[pid] = item

    sources = list(seen.values())
    product_ids = [s["product_id"] for s in sources]
    return product_ids, sources


class AgentGraphWorkflow:
    def __init__(self) -> None:
        self._app = None
        self._lock = Lock()

    def _get_app(self):
        if self._app is None:
            with self._lock:
                if self._app is None:
                    self._app = create_react_agent(
                        model=build_chat_model(),
                        tools=[search_products, search_website_docs],
                        prompt=AGENT_SYSTEM_PROMPT,
                    )
        return self._app

    def run(self, question: str) -> dict:
        result = self._get_app().invoke(
            {"messages": [("user", question)]},
            config={"recursion_limit": 10},
        )
        messages = result.get("messages", [])
        final_answer = messages[-1].content if messages else ""
        product_ids, sources = extract_metadata_from_messages(messages)
        return {
            "answer": final_answer,
            "recommended_product_ids": product_ids,
            "sources": sources,
        }
