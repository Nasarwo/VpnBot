FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY app ./app

RUN pip install --upgrade pip && pip install .

COPY alembic.ini ./

RUN addgroup --system app && adduser --system --ingroup app app
USER app

CMD ["sh", "-c", "alembic upgrade head && python -m app.main"]
