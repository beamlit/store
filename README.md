# Beamlit Store

Repository for managing Beamlit resources, including functions, agents, and tools.

## Overview

This repository serves as a centralized store for Beamlit resources, providing a structured way to manage and deploy various components like functions and agents.

## Project Structure

```
.
├── agents/                 # Agent definitions
├── apps/
│   ├── app-agent/         # Agent application
│   └── app-function/      # Function application
├── functions/             # Function definitions
```

## Development

### Prerequisites

- Docker
- Python with `uv` package manager
- Make

### Available Commands

#### Function Management

```bash
# Run function in development mode
make run-function-dev [function-name]

# Run function in production mode
make run-function [function-name]

# Build function Docker image
make build-function [function-name]

# Run function Docker container
make run-docker-function [function-name]
```

#### Agent Management

```bash
# Run agent in development mode
make run-agent-dev [agent-name]

# Run agent in production mode
make run-agent [agent-name]

# Build agent Docker image
make build-agent [agent-name]

# Run agent Docker container
make run-docker-agent [agent-name]
```

### Development Ports

- Default service port: 1338

## CI/CD

This project uses GitHub Actions for continuous integration and deployment. The workflow configurations can be found in `.github/workflows/`.

## Components

### Agents

The repository includes various agents, such as:

- Langchain Chat Completions Agent

### Functions

The repository includes various functions, such as:

- Beamlit Search: A search engine optimized for comprehensive, accurate, and trusted results. Useful for when you need to answer questions about current events.
- Beamlit Math: A function for performing mathematical calculations.
