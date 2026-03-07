# Stage 1: Builder — lightweight image just for installing deps
FROM python:3.12-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /build

COPY requirements.txt .

RUN uv pip install --no-cache -r requirements.txt --target /deps && \
    find /deps -type d -name "__pycache__" -exec rm -rf {} + && \
    find /deps -type d -name "*.dist-info" -exec rm -rf {} + && \
    find /deps -type d -name "tests" -exec rm -rf {} + && \
    find /deps -type d -name "test" -exec rm -rf {} + && \
    find /deps -type f -name "*.pyc" -delete && \
    find /deps -type f -name "*.pyo" -delete && \
    find /deps -type f -name "*.c" -delete && \
    find /deps -type f -name "*.h" -delete && \
    find /deps -type f -name "py.typed" -delete

# Stage 2: Final Lambda image
FROM public.ecr.aws/lambda/python:3.12-arm64

COPY --from=builder /deps ${LAMBDA_TASK_ROOT}
COPY app/ ${LAMBDA_TASK_ROOT}/app/

CMD ["app.main.lambda_handler"]