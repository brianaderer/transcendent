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

# Run as an ordinary user, not root. The folders the volumes mount onto are created here,
# owned by that user, so new volumes start out writable by it.
RUN useradd --create-home voices \
    && mkdir -p /var/log/voices /home/voices/.cache \
    && chown -R voices /var/log/voices /home/voices/.cache
USER voices
