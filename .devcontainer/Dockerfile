# Dev container for minecraft-manager: Python & Bash
FROM mcr.microsoft.com/devcontainers/python:3.11

# Install bash and common utilities
RUN apt-get update \
    && apt-get install -y bash curl git sudo \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Set up a non-root user (devcontainers convention)
ARG USERNAME=vscode
RUN usermod -aG sudo $USERNAME

# Set workdir
WORKDIR /workspace
