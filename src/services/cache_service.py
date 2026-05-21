import json
from typing import Any

from src.core.config import get_settings
from src.core.redis import get_redis_client


class CacheService:
    def __init__(self) -> None:
        # 모든 key에 prefix를 붙여 다른 서비스 Redis key와 충돌하지 않게 합니다.
        # 예: dripnote-ai:rag-cache:<hash>, dripnote-ai:chat-session:<session-id>
        self.client = get_redis_client()
        self.prefix = get_settings().redis_key_prefix

    def _key(self, namespace: str, key: str) -> str:
        # namespace로 rag-cache, chat-session, index-job 같은 용도를 분리합니다.
        # key 조합 규칙을 한 곳에 모아두면 나중에 prefix 변경이나 멀티테넌트 분리가 쉬워집니다.
        return f"{self.prefix}:{namespace}:{key}"

    def get_json(self, namespace: str, key: str) -> dict[str, Any] | None:
        # Redis에는 JSON 문자열로 저장하고, 호출부에는 dict로 돌려줍니다.
        value = self.client.get(self._key(namespace, key))
        if value is None:
            return None
        return json.loads(value)

    def set_json(
        self,
        namespace: str,
        key: str,
        value: dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        # LLM 관련 캐시는 무기한 보관하지 않도록 TTL을 필수로 받습니다.
        # ensure_ascii=False는 한국어 응답/상품명을 Redis에서 읽기 쉽게 보존하기 위한 설정입니다.
        self.client.setex(
            self._key(namespace, key),
            ttl_seconds,
            json.dumps(value, ensure_ascii=False),
        )
