SHELL := /bin/sh

COMPOSE_FILE := infra/compose/docker-compose.yml
ENV_FILE := .env
COMPOSE := docker compose --env-file $(ENV_FILE) -f $(COMPOSE_FILE)

.DEFAULT_GOAL := help

.PHONY: help bootstrap up down ps logs health config build lint test migrate clean

help: ## Show available commands.
	@awk 'BEGIN {FS = ":.*## "; printf "cryptoAML local commands:\n\n"} /^[a-zA-Z_-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Create .env, start local dependencies, and verify health.
	@./scripts/bootstrap.sh

up: .env ## Start local infrastructure and wait for healthy services.
	@$(COMPOSE) up -d --wait

down: .env ## Stop containers while preserving data volumes.
	@$(COMPOSE) down

ps: .env ## Show local infrastructure status.
	@$(COMPOSE) ps

logs: .env ## Follow local infrastructure logs.
	@$(COMPOSE) logs --follow

health: .env ## Verify PostgreSQL, Garage, and Redpanda.
	@./scripts/healthcheck.sh

config: .env ## Render and validate the Docker Compose configuration.
	@$(COMPOSE) config --quiet

build: config ## Validate the current buildable workspace skeleton.
	@echo "Workspace skeleton is build-ready; component builds will register here."

lint: ## Validate repository structure, shell scripts, and Compose syntax.
	@./scripts/validate-foundation.sh

test: lint ## Run foundation and observability smoke tests.
	@python3 -m unittest discover -s tests -p 'test_*.py'
	@echo "Foundation smoke tests passed."

migrate: .env ## Run registered SQL migrations; succeeds when none exist yet.
	@./scripts/migrate.sh

clean: .env ## Stop containers and remove local volumes (requires CONFIRM=1).
	@if [ "$(CONFIRM)" != "1" ]; then \
		echo "Refusing to remove volumes. Re-run with: make clean CONFIRM=1"; \
		exit 1; \
	fi
	@$(COMPOSE) down --volumes --remove-orphans

.env:
	@cp .env.example .env
	@echo "Created .env from .env.example"
