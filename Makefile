.PHONY: install lint format typecheck test check db-up db-down migrate api bot worker agent-dry-run

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src

test:
	pytest

check: lint typecheck test

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

migrate:
	alembic upgrade head

api:
	vpn-api

bot:
	vpn-bot

worker:
	vpn-worker

agent-dry-run:
	vpn-awg-agent --dry-run
