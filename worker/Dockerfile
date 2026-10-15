FROM python:3.12.14-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f
WORKDIR /app
COPY worker/requirements-linux.lock worker/requirements-linux.lock
RUN python -m pip --isolated install --no-cache-dir --require-hashes --only-binary=:all: -r worker/requirements-linux.lock \
    && python -m pip check
COPY research/pyproject.toml research/pyproject.toml
COPY research/src research/src
COPY contracts contracts
COPY worker/portfolio_worker.py worker/portfolio_worker.py
COPY worker/training_process.py worker/training_process.py
ENV PYTHONPATH=/app/research/src:/app/worker \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp
USER 10001:10001
CMD ["python", "/app/worker/portfolio_worker.py"]
