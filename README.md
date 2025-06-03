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
pip install ansible-scenario-testing
```

## Quick Start

```python
from ansible_playtest.core.runner import run_playbook_test

# Run a test with a scenario
results = run_playbook_test(
    playbook_path='path/to/playbook.yml',
    scenario_path='path/to/scenario.yaml',
    inventory_path='path/to/inventory.yml',
    mock_modules=['service.module1', 'service.module2'],
    use_smtp_mock=True
)

# Check if test passed
if results['success']:
    print("Test passed!")
else:
    print("Test failed!")
    print(f"Details: {results['verification']}")
```

## Documentation

For more detailed information, see the documentation in the [docs/](docs/) directory:

- [Getting Started](docs/getting_started.md)
- [Creating Scenarios](docs/scenarios.md)
- [Configuration Options](docs/configuration.md)
- [Using Verifiers](docs/verifiers.md)
- [Available Mocks](docs/mocks.md)
- [Extending the Framework](docs/customization.md)

## License

MIT
