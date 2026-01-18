.PHONY: help install dev docker-up docker-down migrate migration migration-status migration-history test lint format clean

help:
	@echo "Available commands:"
	@echo "  make install           - Install dependencies"
	@echo "  make dev               - Run development server"
	@echo "  make docker-up         - Start Docker containers"
	@echo "  make docker-down       - Stop Docker containers"
	@echo "  make migrate           - Run database migrations"
	@echo "  make migration         - Create new migration"
	@echo "  make migration-status  - Check migration status"
	@echo "  make migration-history - Show detailed migration history"
	@echo "  make test              - Run tests"
	@echo "  make lint              - Run linting"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean up cache files"

install:
	pip install -r requirements.txt

dev:
	uvicorn app.cmd.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d
	@echo "Waiting for services to start..."
	@sleep 5
	docker-compose exec api alembic upgrade head

start-db: 
	docker-compose up -d db

docker-down:
	docker-compose down

migrate:
	alembic upgrade head

migration:
	@read -p "Enter migration message: " message; \
	alembic revision --autogenerate -m "$$message"

migration-status:
	@echo "Current database revision:"
	@alembic current
	@echo "\nLatest available revision:"
	@alembic heads
	@echo "\nMigration history:"
	@alembic history

migration-history:
	alembic history --verbose

test:
	pytest -v

lint:
	flake8 app/ tests/

format:
	black app/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true

