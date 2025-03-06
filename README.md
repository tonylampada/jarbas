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

## Development

- Run tests: `pytest`
- Format code: `black jarbas tests`
- Sort imports: `isort jarbas tests`
- Type checking: `mypy jarbas tests`

## License

MIT