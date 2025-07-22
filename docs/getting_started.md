# Getting Started with AnsiblePlayTest

AnsiblePlayTest is a powerful framework for testing Ansible playbooks using scenario-based approaches. This guide will help you get started with creating and running your first tests.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Basic Concepts](#basic-concepts)
- [Your First Test](#your-first-test)
- [Project Structure](#project-structure)
- [Running Tests](#running-tests)
- [Command Line Interface](#command-line-interface)
- [Next Steps](#next-steps)

## Prerequisites

Before getting started, ensure you have:

- Python 3.10 or higher
- Ansible 2.9.0 or higher
- Basic understanding of Ansible playbooks and YAML

## Installation

### Using pip

```bash
pip install ansible-playtest
```

### From Source

```bash
git clone <repository-url>
cd ansible-playtest
pip install -e .
```

## Quick Start

Here's a minimal example to get you started quickly:

```python
import pytest

@pytest.mark.playbooks_dir("playbooks")
@pytest.mark.inventory_path("tests/inventory/hosts.ini")
@pytest.mark.scenarios_dir("tests/scenarios/my_scenario.yml")
def test_my_playbook(playbook_path, scenario_path, playbook_runner):
    """Test that demonstrates basic playbook execution."""
    assert playbook_runner.success, f"Playbook failed: {playbook_runner.execution_details}"
```

## Basic Concepts

### Test Scenarios

Scenarios are YAML files that define:
- **Mock responses** for external services
- **Verification criteria** to validate playbook behavior
- **Expected outcomes** (success or failure)

### Module Mocking

Replace Ansible modules with mock implementations to:
- Avoid side effects during testing
- Control module behavior and responses
- Test error conditions

### Verification Strategies

Verify different aspects of playbook execution:
- Module call counts
- Parameter validation
- Call sequences
- Error handling

## Your First Test

Let's create a complete example from scratch.

### 1. Directory Structure

Create the following directory structure:

```
my_ansible_project/
├── playbooks/
│   └── hello_world.yml
├── tests/
│   ├── test_hello_world.py
│   ├── inventory/
│   │   └── hosts.ini
│   └── scenarios/
│       └── hello_world_scenario.yml
└── pytest.ini
```

### 2. Create a Simple Playbook

**playbooks/hello_world.yml**:
```yaml
---
- name: Hello World Playbook
  hosts: localhost
  gather_facts: false
  tasks:
    - name: Ping the host
      ansible.builtin.ping:
      register: ping_result

    - name: Display greeting
      ansible.builtin.debug:
        msg: "Hello, World! Ping was successful: {{ ping_result.ping }}"

    - name: Create a file
      ansible.builtin.copy:
        content: "Hello from Ansible!"
        dest: "/tmp/hello.txt"
```

### 3. Create an Inventory

**tests/inventory/hosts.ini**:
```ini
[test_hosts]
localhost ansible_connection=local
```

### 4. Create a Test Scenario

**tests/scenarios/hello_world_scenario.yml**:
```yaml
---
name: "Hello World Test Scenario"
description: "Tests basic playbook functionality with mocked modules"
playbook: "hello_world.yml"

# Mock responses for modules
service_mocks:
  "ansible.builtin.copy":
    changed: true
    dest: "/tmp/hello.txt"
    mode: "0644"

# Verification criteria
verify:
  # Verify expected module calls
  expected_calls:
    "ansible.builtin.ping": 1
    "ansible.builtin.debug": 1
    "ansible.builtin.copy": 1

  # Verify parameters passed to modules
  parameter_validation:
    ansible.builtin.copy:
      - content: "Hello from Ansible!"
        dest: "/tmp/hello.txt"
```

### 5. Create the Test File

**tests/test_hello_world.py**:
```python
import pytest

@pytest.mark.playbooks_dir("playbooks")
@pytest.mark.inventory_path("tests/inventory/hosts.ini")
class TestHelloWorld:
    """Test class for Hello World playbook."""

    @pytest.mark.scenarios_dir("tests/scenarios/hello_world_scenario.yml")
    def test_hello_world_playbook(self, playbook_path, scenario_path, playbook_runner):
        """Test the Hello World playbook execution."""
        # The playbook_runner fixture automatically runs the playbook with the scenario
        assert playbook_runner.success, (
            f"Playbook execution failed: {playbook_runner.execution_details}"
        )
        
        # Access execution details
        print(f"Playbook success: {playbook_runner.execution_details['playbook_success']}")
        print(f"Verification passed: {playbook_runner.execution_details['verification_passed']}")
```

### 6. Configure pytest

**pytest.ini**:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

## Project Structure

A typical AnsiblePlayTest project follows this structure:

```
project/
├── playbooks/                 # Your Ansible playbooks
│   ├── main_playbook.yml
│   └── library/              # Custom modules (optional)
│       └── custom_module.py
├── tests/                    # Test files and data
│   ├── test_main.py         # Test implementations
│   ├── inventory/           # Test inventories
│   │   └── hosts.ini
│   ├── scenarios/           # Test scenarios
│   │   ├── scenario_01.yml
│   │   └── scenario_02.yml
│   └── mocks/              # Module mocks (optional)
│       ├── ansible.builtin.uri.py
│       └── ansible.builtin.copy.py
├── ansible.cfg             # Ansible configuration
├── pytest.ini             # pytest configuration
└── requirements.txt        # Python dependencies
```

## Running Tests

### Using pytest

Run all tests:
```bash
pytest
```

Run specific test:
```bash
pytest tests/test_hello_world.py::TestHelloWorld::test_hello_world_playbook
```

Run with verbose output:
```bash
pytest -v -s
```

## Advanced Features

### Mock Modules

Create custom mock implementations for specific modules:

**tests/mocks/ansible.builtin.uri.py**:
```python
#!/usr/bin/env python3

def main():
    return {
        "changed": False,
        "status": 200,
        "json": {"message": "Mocked API response"},
        "content": '{"message": "Mocked API response"}'
    }

if __name__ == "__main__":
    print(main())
```

### SMTP Mock Server

Test email functionality with the built-in SMTP mock:

```python
@pytest.mark.smtp_mock_server(port=1025)
def test_email_notification(self, playbook_path, scenario_path, smtp_mock_server, playbook_runner):
    assert playbook_runner.success
    # smtp_mock_server provides access to sent emails
```

### Virtual Environment Testing

Isolate your tests with virtual environments:

```python
@pytest.mark.use_virtualenv
@pytest.mark.requirements_file("requirements-test.txt")
def test_with_isolated_environment(self, playbook_path, scenario_path, playbook_runner):
    assert playbook_runner.success
```

## Common Patterns

### Testing Error Conditions

```yaml
# scenario.yml
---
name: "Error Test Scenario"
expected_failure: true  # Expect the playbook to fail

verify:
  expected_calls:
    "ansible.builtin.fail": 1
```

### Parameterized Tests

```python
@pytest.mark.parametrize("scenario_file", [
    "scenario_dev.yml",
    "scenario_prod.yml",
    "scenario_test.yml"
])
def test_multiple_environments(self, scenario_file, playbook_runner):
    assert playbook_runner.success
```

### Module Sequence Verification

```yaml
# scenario.yml
verify:
  sequence_validation:
    - "ansible.builtin.debug"
    - "ansible.builtin.uri"
    - "ansible.builtin.copy"
```

## Troubleshooting

### Common Issues

1. **Module not found**: Ensure your collections path is set correctly
2. **Scenario not found**: Check the relative path to your scenario files
3. **Verification failures**: Review the verification criteria in your scenario
4. **Permission errors**: Ensure proper file permissions for temporary directories

### Verbose Output

Increase verbosity to see more details:

```bash
pytest -v -s  # For pytest
```

## Next Steps

Now that you've created your first test, explore these advanced topics:

1. **[Scenario Configuration](configuration.md)** - Learn about advanced scenario options
2. **[Verification Strategies](verifier_overview.md)** - Understand different verification methods
3. **[Mock Collections](mock_collections.md)** - Create reusable mock collections
4. **[SMTP Server Mocking](mock_smtp_server.md)** - Test email functionality
5. **[Using Markers](using_markers.md)** - Leverage pytest markers for configuration

## Best Practices

- Keep scenarios focused on specific functionality
- Use descriptive names for tests and scenarios
- Mock external dependencies to avoid side effects
- Verify both positive and negative test cases
- Use virtual environments for isolated testing
- Document your test scenarios clearly

Happy testing with AnsiblePlayTest! 🚀
