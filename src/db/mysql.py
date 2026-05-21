from functools import lru_cache

from src.core.config import get_settings


@lru_cache(maxsize=1)
def get_mysql_engine():
    # SQLAlchemy engine은 단순 커넥션 객체가 아니라 내부에 connection pool을 가집니다.
    # 요청/배치 실행마다 새로 만들면 커넥션이 불필요하게 늘어나므로 프로세스 안에서 하나만 재사용합니다.
    from sqlalchemy import create_engine

    settings = get_settings()
    # AI 서버는 백엔드 서버의 MySQL 8005 포트에 read-only 계정으로 접속합니다.
    # mysql+pymysql dialect를 쓰는 이유는 별도 MySQL C client 설치 없이 Python 패키지만으로 접속하기 위해서입니다.
    url = (
        f"mysql+pymysql://{settings.backend_mysql_user}:"
        f"{settings.backend_mysql_password}@"
        f"{settings.backend_mysql_host}:"
        f"{settings.backend_mysql_port}/"
        f"{settings.backend_mysql_database}"
        "?charset=utf8mb4"
    )
    # pool_pre_ping은 오래 살아 있던 커넥션이 MySQL 서버에서 끊겼는지 사용 전에 확인합니다.
    # pool_recycle은 MySQL wait_timeout에 걸리기 전에 커넥션을 주기적으로 교체해 장시간 실행 배치를 안정화합니다.
    return create_engine(url, pool_pre_ping=True, pool_recycle=1800)
