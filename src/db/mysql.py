from functools import lru_cache

from src.core.config import get_settings


@lru_cache(maxsize=1)
def get_mysql_engine():
    # SQLAlchemy engine은 커넥션 풀을 가지므로 프로세스 안에서 재사용합니다.
    from sqlalchemy import create_engine

    settings = get_settings()
    # AI 서버는 백엔드 서버의 MySQL 8005 포트에 read-only 계정으로 접속합니다.
    url = (
        f"mysql+pymysql://{settings.backend_mysql_user}:"
        f"{settings.backend_mysql_password}@"
        f"{settings.backend_mysql_host}:"
        f"{settings.backend_mysql_port}/"
        f"{settings.backend_mysql_database}"
        "?charset=utf8mb4"
    )
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)
