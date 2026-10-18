FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

WORKDIR /srv
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# Dependencies first, so editing code doesn't reinstall them on every build.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY src ./src
COPY tests ./tests
RUN uv sync --frozen
