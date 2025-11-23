FROM mcr.microsoft.com/devcontainers/python:1-3.12

# Install system dependencies needed for building Python packages and for PDF tools
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    poppler-utils \
    libmagic1 \
    libjpeg-dev \
    zlib1g-dev \
    curl \
    unzip \
    default-jdk-headless \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
 && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1

# Set working directory before switching to non-root user
WORKDIR /workspaces/WjecDocumentScraper

# Use non-root vscode user from base image
USER vscode
