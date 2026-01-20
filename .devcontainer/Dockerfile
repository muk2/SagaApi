FROM mcr.microsoft.com/devcontainers/python:3.13

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /workspace

# Copy dependency files first (Docker cache optimization)
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync
RUN uv sync --frozen

# Copy the rest of the repo
COPY . .

# Set working directory to src for running the app
WORKDIR /workspace/src
