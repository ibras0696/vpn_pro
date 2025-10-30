PROJECT_NAME := vpn_proect
POETRY ?= poetry
PYTHON ?= python3
DOCKER_COMPOSE ?= docker compose
PROJECT_ROOT := $(shell pwd)
UBUNTU_SETUP_OUTPUT ?= ubuntu24_setup.sh

.PHONY: init up down restart ps logs lint fmt test coverage clean clean-docker setup-server ubuntu-setup-script migrate

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

ubuntu-setup-script:
	@cp $(PROJECT_ROOT)/scripts/setup_ubuntu24.sh $(PROJECT_ROOT)/$(UBUNTU_SETUP_OUTPUT)
	@chmod +x $(PROJECT_ROOT)/$(UBUNTU_SETUP_OUTPUT)
	@echo "Скрипт сохранён в $(UBUNTU_SETUP_OUTPUT)"

migrate:
	@echo "Applying database migrations..."
	$(DOCKER_COMPOSE) exec db psql -U postgres -d vpn_project -c "CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, tg_id BIGINT UNIQUE NOT NULL, is_admin BOOLEAN DEFAULT FALSE);"
	$(DOCKER_COMPOSE) exec db psql -U postgres -d vpn_project -c "CREATE TABLE IF NOT EXISTS keys (id SERIAL PRIMARY KEY, uuid VARCHAR(64) UNIQUE NOT NULL, email VARCHAR(255) NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(), expires_at TIMESTAMPTZ, device_limit INTEGER);"
	$(DOCKER_COMPOSE) exec db psql -U postgres -d vpn_project -c "ALTER TABLE IF EXISTS keys ADD COLUMN IF NOT EXISTS device_limit INTEGER;"
