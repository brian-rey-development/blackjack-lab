SHELL := bash
.DEFAULT_GOAL := help

.PHONY: help setup lint format typecheck arch test check notebooks

help: ## List available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-z-]+:.*## / {printf "  %-12s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install every extra and the dev tools, create .env if missing
	uv sync --all-extras --locked
	[ -f .env ] || cp .env.example .env

lint: ## Lint, check formatting and validate notebook structure
	uv run ruff check .
	uv run ruff format --check .
	uv run marimo check notebooks

format: ## Fix lint issues and format in place
	uv run ruff check --fix .
	uv run ruff format .

typecheck: ## Run pyright in strict mode
	uv run pyright

arch: ## Enforce the app > adapters > core layer contracts
	uv run lint-imports

test: ## Run the test suite, notebooks included
	uv run pytest --cov

check: lint typecheck arch test ## Everything CI runs

notebooks: ## Open the marimo notebooks
	uv run marimo edit notebooks
