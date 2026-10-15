# Comic Chaos container image, for local use.
#   docker compose up --build        (see compose.yaml)
#   docker run --rm --env-file .env -p 127.0.0.1:5000:5000 comic-chaos
# The OpenAI key is passed at run time and is never baked into the image.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Unprivileged user; output/ is the only directory the app writes to
# (session checkpoints, and interaction logs if enabled).
RUN useradd --create-home --uid 10001 comic \
    && mkdir -p output \
    && chown comic:comic output
USER comic

# Listen on all interfaces inside the container so the published port
# works. Publish it on 127.0.0.1 only: Comic Chaos has no login.
ENV HOST=0.0.0.0 \
    PORT=5000
EXPOSE 5000

CMD ["python", "main.py"]
