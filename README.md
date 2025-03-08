# Jarbas

A Python project using uv for package management.

## Setup

This project uses [uv](https://github.com/astral-sh/uv) for package management and virtual environment handling.

### Installation

1. Clone the repository
2. Create and activate the virtual environment:
   ```
   uv venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```
   uv pip install -e ".[dev]"
   ```

### Docker Setup

You can run Jarbas using Docker:

1. Build and start the containers:
   ```
   docker-compose up -d
   ```

2. Access the web interface at http://localhost:8501

3. Stop the containers:
   ```
   docker-compose down
   ```

The Docker setup includes:
- Jarbas web interface (default on port 8501)
- Ollama LLM service (on port 11434)

If you need to customize the configuration, edit `config.yaml` before starting the containers.

## Development

- Run tests: `pytest`
- Format code: `black jarbas tests`
- Sort imports: `isort jarbas tests`
- Type checking: `mypy jarbas tests`

## License

MIT 