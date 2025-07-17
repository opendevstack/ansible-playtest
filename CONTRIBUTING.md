# Contributing to AnsiblePlayTest

First off, thank you for considering contributing to AnsiblePlayTest! It's people like you that make this tool better for everyone.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Pull Request Process](#pull-request-process)
- [Coding Style](#coding-style)
- [Testing](#testing)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)
- [Documentation](#documentation)

## Code of Conduct

This project and everyone participating in it are governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/ansible-playtest.git`
3. Create a branch for your changes: `git checkout -b feature/your-feature-name`
4. Install development dependencies: `pip install -r requirements_dev.txt`

## Development Environment

We recommend setting up a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements_dev.txt
```

## Project Structure

- `ansible_playtest/` - Core module code
- `docs/` - Documentation
- `examples/` - Example playbooks and scenarios
- `tests/` - Test suite

## Pull Request Process

1. Update the documentation if needed
2. Add or update tests as necessary
3. Ensure your code passes all tests: `pytest`
4. Make sure code coverage doesn't decrease: `pytest --cov=ansible_playtest`
5. Submit your pull request
6. Address any feedback from maintainers

## Coding Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Write docstrings for all functions, classes, and modules
- Use descriptive variable names
- Keep functions focused on a single responsibility

## Testing

All new code should come with tests. We use pytest for testing:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ansible_playtest
```

## Reporting Bugs

Use the GitHub issue tracker to report bugs. Please include:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant logs or error messages
- Your environment (OS, Python version, Ansible version)

## Feature Requests

Feature requests are welcome! Please use the GitHub issue tracker and:

1. Use a clear, descriptive title
2. Describe the current behavior and explain why it's insufficient
3. Describe the desired behavior
4. Explain why this feature would benefit most users

## Documentation

Documentation improvements are always welcome! We maintain documentation in the `docs/` directory.

When updating documentation:
- Follow the existing style
- Use Markdown for all documentation files
- Keep examples clear and concise