# AnsiblePlayTest

A flexible and extensible framework for testing Ansible playbooks using scenario-based approaches.

## Features

- **Scenario-based testing:** Define test scenarios in YAML files
- **Service mocking:** Mock external services that your playbooks interact with
- **Verification strategies:** Verify module calls, parameters, call sequences, and errors
- **SMTP server mock:** Built-in mock SMTP server for testing email notifications
- **Advanced test classes:** Enhanced test classes with additional capabilities
- **Parameterized tests:** Run the same test with different parameters
- **Fluent API:** Build complex scenarios programmatically

## Installation

```bash
pip install ansible-playtest
```
- [Getting Started](docs/getting_started.md)


## Documentation

For detailed information, see the documentation in the [docs/](docs/) directory:

- [Creating Scenarios](docs/scenarios.md)
- [Configuration Options](docs/configuration.md)
- [Using Verifiers](docs/verifiers_overview.md)
- [Available Mocks](docs/mocks.md)

## Development


### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ansible_playtest
```

