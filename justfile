# Install all dependencies
install:
    uv sync --all-groups

# Run tests
test:
    uv run --group test pytest

# Run tests with coverage
test-cov:
    uv run --group test pytest --cov=src --cov=tests --cov-report=xml

# Run unit tests only
test-unit:
    uv run --group test pytest -m "unit or (not integration and not end_to_end)"

# Run end-to-end tests only
test-e2e:
    uv run --group test pytest -m end_to_end

# Run type checking
typing:
    uv run --group typing ty check

# Run linting and formatting
lint:
    uvx --with pre-commit-uv pre-commit run -a

# Run all checks (format, lint, typing, test)
check: lint typing test

# Run tests with lowest dependency resolution
test-lowest:
    uv run --group test --resolution lowest-direct pytest

# Run tests with highest dependency resolution
test-highest:
    uv run --group test --resolution highest pytest

# Build package
build:
    uv build
