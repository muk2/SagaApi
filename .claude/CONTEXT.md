# Claude Code Context for SagaApi

This file provides context for Claude Code sessions, including Ralph Loop.

## Project Structure

```
SagaApi/
├── src/               # Python source code
│   ├── services/      # Business logic
│   ├── repositories/  # Data access
│   └── ...
├── tests/             # Test files
├── .devcontainer/     # Dev container config
└── ralph-tasks/       # Task definitions for Ralph
```

## Development Environment

### Dev Container
- **Container name**: `sagaapi-devcontainer-app-1`
- **Working directory**: `/workspace` (mounted from project root)
- **Database**: PostgreSQL at `db:5432`
- **Python version**: 3.13
- **Key tools**: pytest, ruff, uvicorn

### Starting Container
```bash
docker compose -f .devcontainer/docker-compose.yml up -d
```

### Checking Container Status
```bash
docker ps | grep sagaapi-devcontainer
```

## Command Execution Rules

### Run in Dev Container
Use `docker exec` for Python/testing/linting:

```bash
# Run tests
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest"

# Run linting
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"

# Run coverage
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest --cov=src"

# Run app
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && uvicorn main:app"
```

### Run on Host
Git and GitHub CLI run normally:

```bash
# Git commands
git status
git add .
git commit -m "message"
git push

# GitHub CLI
gh pr create
gh pr list
gh pr view 123
```

### File Operations
Files are shared between host and container via mount. Edit normally - changes are visible in both places.

## Code Quality Standards

### Testing
- Use `pytest` for tests
- Use `pytest-asyncio` for async tests
- Use `httpx` for FastAPI test client
- Aim for >= 80% coverage
- Put tests in `tests/` directory

### Linting
- Use `ruff` for linting: `ruff check src/`
- Fix linting errors before committing
- Follow existing code style

### Database
- Connection string: `postgresql://sagaapi:sagaapi_dev@db:5432/sagaapi`
- Use SQLAlchemy for ORM
- Migrations (if applicable)

## Git Workflow

### Branch Naming
- Feature: `ralph/add-<feature>`
- Fix: `ralph/fix-<issue>`
- Test: `ralph/test-<area>`

### Commit Messages
- Format: `[ralph] <description>`
- Be descriptive but concise
- Example: `[ralph] Add auth endpoint tests with edge cases`

### PR Creation
```bash
# Create draft PR
gh pr create --base main --head <branch> --title "<title>" --body "<description>" --draft

# Mark as ready
gh pr ready <pr-number>
```

## Project Conventions

See `.claude/CLAUDE.md` for:
- Senior software architect mindset
- System thinking approach
- Production-ready standards
- Avoiding over-engineering

## Ralph Loop Workflow

See `.claude/RALPH-WORKFLOW.md` for detailed Ralph Loop workflow including:
- Development phases
- PR creation and review
- Self-review process
- Iteration strategy
- Quality standards

## Common Tasks

### Run All Tests
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest tests/"
```

### Check Code Quality
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && ruff check src/"
```

### Generate Coverage Report
```bash
docker exec -it sagaapi-devcontainer-app-1 bash -c "cd /workspace && pytest --cov=src --cov-report=html"
```

### Access Database
```bash
docker exec -it sagaapi-devcontainer-db-1 psql -U sagaapi -d sagaapi
```

## Important Notes

- **API keys on host**: ANTHROPIC_API_KEY stays on host machine (secure)
- **Files are shared**: Changes in container appear on host and vice versa
- **Container must be running**: Start it if commands fail
- **Git on host**: All git operations run on host, not in container
