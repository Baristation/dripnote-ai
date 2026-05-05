from functools import lru_cache

from src.core.config import get_settings


@lru_cache(maxsize=1)
def get_redis_client():
    # Redis는 LLM 세션/캐시/rate limit/job status를 위한 AI 서버 전용 저장소입니다.
    import redis

    settings = get_settings()
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password or None,
        decode_responses=True,
    )
