from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from openai import APIConnectionError, AuthenticationError, PermissionDeniedError, RateLimitError
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse
from redis.exceptions import RedisError
from sqlalchemy.exc import OperationalError

from apps.api.routes.chat import router as chat_router
from apps.api.routes.rag import router as rag_router
from apps.api.routes.training import router as training_router
from src.core.config import get_settings


# 환경변수를 읽어서 앱 설정 객체를 만듭니다.
# 이 시점에는 OpenAI/Qdrant/MySQL client를 만들지 않고, 앱 이름처럼 가벼운 설정만 사용합니다.
settings = get_settings()

# FastAPI 앱 생성 후 기능별 라우터를 연결합니다.
# 라우터 prefix를 /api로 통일해 백엔드나 프론트에서 API gateway처럼 붙이기 쉽게 합니다.
app = FastAPI(title=settings.app_name)
app.include_router(chat_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(training_router, prefix="/api")


@app.exception_handler(RateLimitError)
async def openai_rate_limit_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    # OpenAI rate limit은 일시적 장애로 보고 503과 Retry-After를 반환합니다.
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "OpenAI rate limit exceeded. Please retry later."},
        headers={"Retry-After": "30"},
    )


@app.exception_handler(AuthenticationError)
@app.exception_handler(PermissionDeniedError)
async def openai_auth_handler(
    request: Request,
    exc: AuthenticationError | PermissionDeniedError,
) -> JSONResponse:
    # 키/프로젝트/모델 권한 문제는 클라이언트 입력 문제가 아니라 서버 설정 문제입니다.
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={"detail": "OpenAI credentials or model permissions are invalid."},
    )


@app.exception_handler(APIConnectionError)
async def openai_connection_handler(request: Request, exc: APIConnectionError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "OpenAI service is temporarily unavailable."},
    )


@app.exception_handler(OperationalError)
async def mysql_operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Backend MySQL is temporarily unavailable."},
    )


@app.exception_handler(UnexpectedResponse)
@app.exception_handler(ResponseHandlingException)
async def qdrant_error_handler(
    request: Request,
    exc: UnexpectedResponse | ResponseHandlingException,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Vector database is temporarily unavailable."},
    )


@app.exception_handler(RedisError)
async def redis_error_handler(request: Request, exc: RedisError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Redis is temporarily unavailable."},
    )


# 서버 상태 확인용 엔드포인트입니다.
# 외부 의존성(OpenAI, MySQL, Qdrant)을 호출하지 않는 lightweight healthcheck라 컨테이너 기동 확인에 적합합니다.
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
