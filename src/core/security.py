from fastapi import Header, HTTPException, status

from src.core.config import get_settings


def require_internal_key(x_internal_key: str = Header(default="")) -> None:
    # 인덱싱/훈련처럼 비용이 크거나 위험한 내부 API는 shared secret으로 보호합니다.
    # INTERNAL_API_KEY가 비어 있으면 안전하게 모든 요청을 거부해 운영 실수를 줄입니다.
    expected = get_settings().internal_api_key
    if not expected or x_internal_key != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
