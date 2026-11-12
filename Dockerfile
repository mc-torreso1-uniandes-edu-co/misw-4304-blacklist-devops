FROM public.ecr.aws/docker/library/python:3.13.16-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY application.py ./

ARG VERSION=local
RUN printf '%s\n' "$VERSION" > VERSION

RUN useradd --uid 10001 --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "--bind", ":8000", "--workers", "2", "application:application"]
