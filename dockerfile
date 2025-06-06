FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*


COPY pyproject.toml ./

RUN pip install .

COPY src/ ./src/

EXPOSE 8000

CMD ["python", "src/server.py", "--transport", "stdio"]
