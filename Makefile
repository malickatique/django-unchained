# =============================================================================
# django-unchained — Development Makefile
# =============================================================================
# Usage: make <target>
# Run `make help` to list all available targets with descriptions.
# =============================================================================

.DEFAULT_GOAL := help
.PHONY: help \
        deps-compile deps-compile-base deps-compile-dev deps-compile-test deps-compile-prod \
        deps-sync deps-sync-test deps-sync-prod \
        deps-upgrade deps-upgrade-package \
        run migrate migrations shell test lint format typecheck \
        createsuperuser collectstatic clean

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

help: ## Show this help message
	@echo ""
	@echo "django-unchained — available targets"
	@echo "======================================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-28s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ---------------------------------------------------------------------------
# Dependency management (pip-tools)
# ---------------------------------------------------------------------------

deps-compile: deps-compile-base deps-compile-dev deps-compile-test deps-compile-prod ## Compile all .in → .txt lock files (run after editing any .in file)

deps-compile-base: ## Compile requirements/base.in → base.txt
	pip-compile requirements/base.in \
		--output-file requirements/base.txt \
		--no-strip-extras \
		--quiet

deps-compile-dev: ## Compile requirements/development.in → development.txt
	pip-compile requirements/development.in \
		--output-file requirements/development.txt \
		--no-strip-extras \
		--quiet

deps-compile-test: ## Compile requirements/test.in → test.txt
	pip-compile requirements/test.in \
		--output-file requirements/test.txt \
		--no-strip-extras \
		--quiet

deps-compile-prod: ## Compile requirements/production.in → production.txt
	pip-compile requirements/production.in \
		--output-file requirements/production.txt \
		--no-strip-extras \
		--quiet

deps-sync: ## Sync local dev environment from development.txt (like npm ci)
	pip-sync requirements/development.txt

deps-sync-test: ## Sync environment from test.txt (for CI)
	pip-sync requirements/test.txt

deps-sync-prod: ## Sync environment from production.txt (for production)
	pip-sync requirements/production.txt

deps-upgrade: ## Upgrade ALL packages to latest allowed versions and recompile
	pip-compile --upgrade requirements/base.in        --output-file requirements/base.txt        --no-strip-extras --quiet
	pip-compile --upgrade requirements/development.in --output-file requirements/development.txt --no-strip-extras --quiet
	pip-compile --upgrade requirements/test.in        --output-file requirements/test.txt        --no-strip-extras --quiet
	pip-compile --upgrade requirements/production.in  --output-file requirements/production.txt  --no-strip-extras --quiet
	pip-sync requirements/development.txt
	@echo "All packages upgraded. Review changes with: git diff requirements/"

deps-upgrade-package: ## Upgrade ONE package: make deps-upgrade-package PKG=django
ifndef PKG
	$(error PKG is not set. Usage: make deps-upgrade-package PKG=django)
endif
	pip-compile --upgrade-package $(PKG) requirements/base.in --output-file requirements/base.txt --no-strip-extras --quiet
	pip-compile --upgrade-package $(PKG) requirements/development.in --output-file requirements/development.txt --no-strip-extras --quiet
	pip-compile --upgrade-package $(PKG) requirements/test.in --output-file requirements/test.txt --no-strip-extras --quiet
	pip-compile --upgrade-package $(PKG) requirements/production.in --output-file requirements/production.txt --no-strip-extras --quiet
	pip-sync requirements/development.txt
	@echo "Upgraded $(PKG) across all environments."

# ---------------------------------------------------------------------------
# Django management
# ---------------------------------------------------------------------------

run: ## Start the development server (http://127.0.0.1:8000)
	python manage.py runserver

migrate: ## Apply database migrations
	python manage.py migrate

migrations: ## Create new migrations for changed models
	python manage.py makemigrations

shell: ## Open the Django interactive shell (uses ipython if installed)
	python manage.py shell

createsuperuser: ## Create a Django superuser
	python manage.py createsuperuser

collectstatic: ## Collect static files to STATIC_ROOT
	python manage.py collectstatic --noinput

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: ## Run the full test suite
	pytest

test-fast: ## Run tests in parallel (-n auto) with fail-fast
	pytest -n auto -x

test-cov: ## Run tests with coverage report
	pytest --cov=. --cov-report=term-missing --cov-report=html

# ---------------------------------------------------------------------------
# Code quality
# ---------------------------------------------------------------------------

lint: ## Run ruff linter (check only, no fix)
	ruff check .

format: ## Run ruff formatter + auto-fix lint issues
	ruff format .
	ruff check . --fix

typecheck: ## Run mypy static type checker
	mypy .

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

clean: ## Remove Python cache files and build artefacts
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleaned."
