from fastapi import FastAPI

from apps.api.routes.chat import router as chat_router
from apps.api.routes.rag import router as rag_router
from apps.api.routes.training import router as training_router
from src.core.config import get_settings


# 환경변수를 읽어서 앱 설정 객체를 만든다.
settings = get_settings()

# FastAPI 앱 생성 후 기능별 라우터를 연결한다.
app = FastAPI(title=settings.app_name)
app.include_router(chat_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(training_router, prefix="/api")


# 서버 상태 확인용 엔드포인트
@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
