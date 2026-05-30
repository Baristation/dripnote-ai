from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # FastAPI 앱 이름과 실행 환경입니다.
    # app_name은 Swagger 문서 제목으로도 쓰이고, app_env는 추후 local/dev/prod 분기에 사용할 수 있습니다.
    app_name: str = "dripnote-ai"
    app_env: str = "local"
    # 관리자성 내부 API를 보호하는 단순 shared secret입니다.
    # 로컬에서는 .env에만 두고, 운영에서는 secret manager나 배포 환경변수로 주입합니다.
    internal_api_key: str = ""

    # OpenAI 호출에 필요한 설정입니다.
    # BaseSettings 규칙에 따라 .env의 OPENAI_API_KEY, OPENAI_MODEL, EMBEDDING_MODEL 값이 여기에 매핑됩니다.
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    # 상품 전체를 한 번에 embedding하면 OpenAI TPM 제한을 넘을 수 있어 batch 크기를 설정으로 둡니다.
    embedding_batch_size: int = 8

    # 학습/파인튜닝 계열 코드에서 사용할 디바이스입니다.
    # 현재 Docker 기본 이미지는 가볍게 유지하려고 CPU 기준으로 두고, GPU 학습은 별도 옵션으로 확장합니다.
    train_device: str = "cpu"

    # Qdrant는 상품 문서 embedding을 저장하는 Vector DB입니다.
    # Docker compose 내부에서는 qdrant 서비스명을 hostname으로 쓰므로 QDRANT_URL=http://qdrant:6333 형태가 됩니다.
    qdrant_url: str = "http://localhost:6333"
    # 로컬 Qdrant는 보통 API key 없이 띄웁니다. Qdrant Cloud나 인증 프록시를 쓰면 값이 필요합니다.
    qdrant_api_key: str = ""
    # collection은 MySQL의 table에 가까운 단위입니다. 여기에는 상품 추천용 vector point가 들어갑니다.
    qdrant_collection: str = "baristation-products"
    # embedding vector 차원입니다. text-embedding-3-small은 1536차원이므로 collection 생성 시 이 값과 맞아야 합니다.
    qdrant_vector_size: int = 1536
    # 검색 한 번에 가져올 상품 후보 수입니다. 값이 커질수록 LLM context도 길어집니다.
    qdrant_top_k: int = 5

    # Redis는 당장 필수 RAG 저장소는 아니지만, LLM 응답 캐시/세션/checkpoint/rate-limit 용도로 확장하기 위해 둡니다.
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_key_prefix: str = "dripnote-ai"

    # AI 서버는 자체 MySQL을 띄우지 않고 백엔드 서버의 MySQL을 read-only 계정으로 읽습니다.
    # 현재 백엔드 MySQL은 외부 8005 포트로 열려 있고, 실제 DB명은 .env에서 BACKEND_MYSQL_DATABASE=dripnote로 덮어씁니다.
    backend_mysql_host: str = "localhost"
    backend_mysql_port: int = 8005
    backend_mysql_database: str = "baristation"
    backend_mysql_user: str = "ai_readonly"
    backend_mysql_password: str = ""

    # SettingsConfigDict는 BaseSettings에게 .env 파일을 읽으라고 알려주는 설정입니다.
    # 환경변수 값이 있으면 기본값보다 우선하고, 문자열 숫자도 int 필드에 맞게 자동 변환됩니다.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # 설정은 실행 중 자주 참조되므로 한 번 만든 Settings 객체를 재사용합니다.
    # 테스트에서 환경변수를 바꿔 다시 읽어야 할 때는 get_settings.cache_clear()를 호출하면 됩니다.
    return Settings()
