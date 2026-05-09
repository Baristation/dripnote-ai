from functools import lru_cache

from src.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client():
    # Redis는 LLM 세션/캐시/rate limit/job status를 위한 AI 서버 전용 저장소입니다.
    # client도 connection pool을 내부적으로 관리하므로 매 호출마다 새로 만들지 않고 캐시합니다.
    import redis

    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        # 문자열 값을 bytes가 아니라 str로 바로 받으면 JSON cache service에서 후처리가 단순해집니다.
        decode_responses=True,
    )
