FROM python:3.11-slim AS runtime

# 컨테이너에서 .pyc 파일을 만들지 않고 로그를 즉시 stdout으로 흘려보냅니다.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# curl은 Docker healthcheck에 쓰고, build-essential은 일부 Python 패키지 빌드에 필요할 수 있습니다.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl build-essential \
    && rm -rf /var/lib/apt/lists/*

# 먼저 프로젝트 메타데이터와 소스만 복사해 패키지 설치 레이어를 구성합니다.
COPY pyproject.toml README.md ./
COPY apps ./apps
COPY src ./src
COPY scripts ./scripts

# 로컬 개발 이미지는 INSTALL_EXTRAS="[dev]"로 pytest/ruff를 포함하고,
# 운영 이미지는 빈 값으로 설치해 dev 의존성을 제외할 수 있습니다.
ARG INSTALL_EXTRAS="[dev]"
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir ".${INSTALL_EXTRAS}"

EXPOSE 8000

# FastAPI 앱의 /health가 200을 반환하는지 Docker가 직접 확인합니다.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
