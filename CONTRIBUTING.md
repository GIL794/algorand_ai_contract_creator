# Contributing to Algorand AI Contract Creator

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/CDNamchu/algorand_ai_contract_creator.git
cd algorand_ai_contract_creator
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install in Development Mode

```bash
pip install -e .
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

## Project Structure

```
src/algorand_ai_contractor/    # Main package
├── core/                       # Core business logic
├── contracts/                  # Contract templates & config
└── ui/                         # User interfaces

tests/                          # Test suite
scripts/                        # Utility scripts
outputs/                        # Generated artifacts (gitignored)
docs/                          # Documentation
```

## Code Style

- Follow PEP 8 guidelines
- Use Black for code formatting: `black src/ tests/`
- Use type hints where appropriate
- Write docstrings for all public functions/classes
- Keep line length to 100 characters

## Testing

Run tests before submitting:

```bash
pytest tests/
```

## Pull Request Process

1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes
3. Run tests and linting
4. Commit with clear messages
5. Push and create a Pull Request

## Coding Standards

- **Imports**: Group in order: stdlib, third-party, local
- **Functions**: Keep functions focused and under 50 lines
- **Classes**: Use clear, descriptive names
- **Comments**: Explain *why*, not *what*
- **Error Handling**: Use specific exceptions

## Questions?

Open an issue for:
- Bug reports
- Feature requests
- Documentation improvements
- Questions about usage

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
