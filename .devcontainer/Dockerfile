FROM mcr.microsoft.com/devcontainers/python:1-3.13-bookworm

# Install system dependencies
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    postgresql-client \
    build-essential \
    libpq-dev \
    curl \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch to vscode user for installations
USER vscode

# Install Rust for ralph-orchestrator
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal
ENV PATH="/home/vscode/.cargo/bin:${PATH}"

# Install ralph-orchestrator
RUN cargo install ralph-orchestrator

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Install Python linting/formatting tools globally
RUN pip install --user --no-cache-dir ruff pytest pytest-asyncio pytest-cov httpx

# Set working directory
WORKDIR /workspace

# Install project Python dependencies (will be run in postCreateCommand)
# COPY requirements.txt /tmp/
# RUN pip install --user --no-cache-dir -r /tmp/requirements.txt

CMD ["sleep", "infinity"]
