FROM ghcr.io/astral-sh/uv:0.13.6 AS uv
FROM python:3.12-alpine3.23

COPY --from=uv /uv /usr/local/bin/uv
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    DATABASE_PATH=/data/db.sqlite3 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN apk upgrade --no-cache
RUN uv sync --locked --no-dev --no-install-project --no-managed-python --no-cache
COPY manage.py ./
COPY config ./config
COPY timetable ./timetable
COPY docker-entrypoint.sh ./
RUN addgroup -g 10001 app \
    && adduser -D -H -u 10001 -G app app \
    && mkdir /data \
    && chown app:app /data \
    && chmod +x /app/docker-entrypoint.sh
USER app
EXPOSE 8000
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "60", "--access-logfile", "-"]
