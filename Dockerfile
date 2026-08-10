FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY src ./src
COPY tests ./tests

# Compose supplies article-specific arguments. Override the entrypoint with
# `python` when running test or other development commands.
ENTRYPOINT ["python", "-m", "wiki_kg.cli"]
CMD ["Federer–Nadal rivalry", "--max-sentences", "100", "--output", "knowledge_graph.html"]
