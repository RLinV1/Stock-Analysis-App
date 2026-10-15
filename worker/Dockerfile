FROM python:3.12.14-slim
WORKDIR /app
COPY research/requirements-cpu.txt research/requirements-cpu.txt
COPY worker/requirements.txt worker/requirements.txt
RUN python -m pip install --no-cache-dir -r research/requirements-cpu.txt -r worker/requirements.txt
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
