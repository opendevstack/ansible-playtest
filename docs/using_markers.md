# Using Markers with Ansible Playtest

This document explains how to use pytest markers to configure Ansible Playtest options for your tests.

## Available Markers

The Ansible Playtest plugin provides the following markers:

### Directory and Path Markers

- `@pytest.mark.scenarios_dir(path)` - Specifies the directory containing scenario files
- `@pytest.mark.playbooks_dir(path)` - Specifies the directory containing playbooks to test
- `@pytest.mark.inventory_path(path)` - Specifies the path to the inventory file
- `@pytest.mark.mock_collections_dir(path)` - Specifies path to mock collections directory

### Environment Markers

- `@pytest.mark.use_virtualenv(requirements=None)` - Run the playbook in a virtual environment
- `@pytest.mark.ansible_cfg_path(path)` - Specifies a custom ansible.cfg file

### Test Behavior Markers

- `@pytest.mark.keep_artifacts` - Keep test artifacts after test completion
- `@pytest.mark.ansible_scenario(name)` - Identify a test as an Ansible scenario test

### Mock Service Markers

- `@pytest.mark.mock_modules(modules)` - Mock the specified list of Ansible modules
- `@pytest.mark.smtp_mock_server(port=1025)` - Enable SMTP mock server

## Applying Markers

Markers can be applied at different levels:

### Function Level

Apply a marker to a specific test function:

```python
@pytest.mark.scenarios_dir("./specific_scenarios")
def test_playbook(playbook_path, scenario_path, playbook_runner):
    assert playbook_runner.success
```

### Class Level

Apply markers to all test methods in a class:

```python
@pytest.mark.scenarios_dir("./class_scenarios")
@pytest.mark.playbooks_dir("./class_playbooks")
class TestAnsiblePlaybooks:
    def test_playbook(self, playbook_path, scenario_path, playbook_runner):
        assert playbook_runner.success
```

### Module Level

Apply markers to all tests in a module using `pytestmark`:

```python
import pytest

pytestmark = [
    pytest.mark.scenarios_dir("./module_scenarios"),
    pytest.mark.playbooks_dir("./module_playbooks")
]
```

## Markers vs. Command-Line Options

Markers have higher precedence than command-line options. The resolution order is:

1. Function-level markers
2. Class-level markers  
3. Module-level markers
4. Command-line options
5. Default values

## Examples

### Using Directory Markers

```python
import pytest

@pytest.mark.scenarios_dir("./custom_scenarios")
@pytest.mark.playbooks_dir("./custom_playbooks")
def test_ansible_playbook(playbook_path, scenario_path, playbook_runner):
    assert playbook_runner.success
```

### Running a Playbook in a Virtual Environment

```python
@pytest.mark.use_virtualenv(requirements="requirements.txt")
def test_with_virtualenv(playbook_path, scenario_path, playbook_runner):
    assert playbook_runner.success
```

### Using Mock SMTP Server

```python
@pytest.mark.smtp_mock_server(port=2025)
def test_with_smtp_mock(playbook_path, scenario_path, smtp_mock_server, playbook_runner):
    # Test will have access to the smtp_mock_server fixture
    assert len(smtp_mock_server.messages) > 0
    assert playbook_runner.success
```

### Using Multiple Markers

```python
@pytest.mark.scenarios_dir("./email_scenarios")
@pytest.mark.smtp_mock_server()  # Use default port
@pytest.mark.keep_artifacts  # Keep test artifacts for debugging
def test_email_playbook(playbook_path, scenario_path, smtp_mock_server, playbook_runner):
    assert playbook_runner.success
    assert len(smtp_mock_server.messages) > 0
```

## See Also

- [Configuration Guide](configuration.md) - More information about Ansible Playtest configuration
- [Using Markers Example](../examples/using_markers/README.md) - Example code using markers
