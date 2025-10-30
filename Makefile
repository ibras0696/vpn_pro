PROJECT_NAME := vpn_proect
POETRY ?= poetry
PYTHON ?= python3
DOCKER_COMPOSE ?= docker compose
PROJECT_ROOT := $(shell pwd)

.PHONY: init up down restart ps logs lint fmt test coverage clean clean-docker setup-server

init:
	@cp -n .env.example .env || true
	$(POETRY) install

up:
	$(DOCKER_COMPOSE) up --build -d

down:
	$(DOCKER_COMPOSE) down

restart: down up

ps:
	$(DOCKER_COMPOSE) ps

logs:
	$(DOCKER_COMPOSE) logs -f bot

lint:
	$(POETRY) run ruff check .

fmt:
	$(POETRY) run ruff check --fix .

test:
	$(POETRY) run pytest -q --disable-warnings

coverage:
	$(POETRY) run coverage run -m pytest
	$(POETRY) run coverage report

clean:
	@echo "Removing Python cache files and reports..."
	@find . -name "__pycache__" -type d -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage coverage.xml htmlcov dist build

clean-docker:
	$(DOCKER_COMPOSE) down -v --remove-orphans

setup-server:
	@$(PROJECT_ROOT)/scripts/setup_server.sh
