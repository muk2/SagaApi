#!/bin/bash
set -e

echo "🚀 Setting up SagaApi development environment..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install project dependencies
if [ -f "src/requirements.txt" ]; then
    pip install -r src/requirements.txt
fi

# Install development dependencies
pip install pytest pytest-asyncio pytest-cov httpx ruff black isort

# Verify ralph is installed
if ! command -v ralph &> /dev/null; then
    echo "⚠️  Ralph not found, installing..."
    cargo install ralph-orchestrator
fi

# Verify Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "⚠️  Claude Code not found, installing..."
    npm install -g @anthropic-ai/claude-code
fi

# Wait for database to be ready
echo "⏳ Waiting for PostgreSQL..."
until pg_isready -h db -U sagaapi > /dev/null 2>&1; do
    sleep 1
done

echo "✅ Database ready!"

# Create ralph-tasks directory if it doesn't exist
mkdir -p ralph-tasks

# Initialize git config if not set (for commits)
if [ -z "$(git config --global user.email)" ]; then
    echo "⚠️  Git user.email not set. Ralph may need this for commits."
fi

echo "✅ Development environment ready!"
echo ""
echo "Quick start commands:"
echo "  - Run API: uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo "  - Run tests: pytest"
echo "  - Initialize Ralph: cd ralph-tasks && ralph init --backend claude"
echo "  - Run Ralph overnight: ./ralph-tasks/run-overnight.sh"
