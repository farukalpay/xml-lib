.PHONY: help dev test publish clean lint format typecheck coverage install

help: ## Show this help message
	@echo "xml-lib Makefile targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -e .

dev: install ## Set up development environment
	@echo "Development environment ready!"
	@echo "Run 'make test' to run tests"
	@echo "Run 'make lint' to check code quality"

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ -v --cov=xml_lib --cov-report=html --cov-report=term
	@echo "Coverage report generated in htmlcov/"

test-quick: ## Run quick tests (skip slow tests)
	pytest tests/ -v -m "not slow"

validate: ## Validate all XML files in the project
	xml-lib validate . --output out/assertions.xml --jsonl out/assertions.jsonl

validate-strict: ## Validate with strict mode (warnings as errors)
	xml-lib validate . --strict --output out/assertions.xml --jsonl out/assertions.jsonl

publish: ## Publish XML to HTML documentation
	xml-lib publish . --output-dir out/site
	@echo "Documentation published to out/site/"
	@echo "Open out/site/index.html in your browser"

publish-pptx: ## Render example document to PowerPoint
	xml-lib render-pptx example_document.xml --output out/presentation.pptx
	@echo "PowerPoint created at out/presentation.pptx"

diff: ## Show diff between example documents
	xml-lib diff example_document.xml example_amphibians.xml --explain

lint: ## Lint code with ruff
	ruff check cli/

format: ## Format code with black
	black cli/ tests/

format-check: ## Check code formatting
	black --check cli/ tests/

typecheck: ## Type check with mypy
	mypy cli/ --ignore-missing-imports

coverage: test-cov ## Generate coverage report
	@echo "Opening coverage report..."
	@python -m webbrowser htmlcov/index.html 2>/dev/null || open htmlcov/index.html 2>/dev/null || xdg-open htmlcov/index.html 2>/dev/null || echo "Open htmlcov/index.html manually"

clean: ## Clean build artifacts
	rm -rf build/ dist/ *.egg-info
	rm -rf out/
	rm -rf store/
	rm -rf htmlcov/ .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

clean-all: clean ## Clean everything including virtual environments
	rm -rf venv/ .venv/

benchmark: ## Run performance benchmarks
	@echo "Running validation benchmark on 1k documents..."
	@python tests/benchmark.py

ci: lint typecheck test ## Run all CI checks locally

pre-commit: format lint typecheck test ## Run pre-commit checks

# Docker targets
docker-build: ## Build Docker image
	docker build -t xml-lib:latest .

docker-run: ## Run xml-lib in Docker
	docker run --rm -v $(PWD):/workspace xml-lib:latest xml-lib validate /workspace

# Release targets
release-patch: ## Bump patch version and create release
	@echo "Bumping patch version..."
	@# Add version bump logic here

release-minor: ## Bump minor version and create release
	@echo "Bumping minor version..."
	@# Add version bump logic here

release-major: ## Bump major version and create release
	@echo "Bumping major version..."
	@# Add version bump logic here
