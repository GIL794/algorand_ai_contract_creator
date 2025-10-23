# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Reorganized project structure to follow Python best practices
- Moved source code to `src/algorand_ai_contractor/` layout
- Renamed `tools/` to `core/` for better clarity
- Separated outputs into dedicated `outputs/` directory
- Updated imports to use new package structure

### Added
- Created professional directory structure
- Added CONTRIBUTING.md with development guidelines
- Added requirements-dev.txt for development dependencies
- Improved .gitignore patterns
- Added proper package __init__.py files with docstrings

## [0.1.0] - 2025-10-23

### Added
- Initial release
- AI-powered PyTeal smart contract generation
- Natural language to contract conversion
- Multi-layer validation (syntax, security, compilation)
- TestNet deployment capabilities
- Streamlit web interface
- Audit trail and logging
- AlgoKit integration
