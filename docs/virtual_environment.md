# Virtual Environment Support

The `ansible-playtest` framework includes robust virtual environment support to ensure that tests can be run in isolated environments with all necessary dependencies, including mock servers.

## Overview

The `VirtualEnvironment` class in the `ansible_playbook_runner.environment` module provides comprehensive support for:

- Creating Python virtual environments
- Installing packages and requirements
- Installing the `ansible_playtest` package with mock servers
- Running commands within the virtual environment
- Cleaning up the environment when it is no longer needed

## Making Mock Servers Available

When creating a virtual environment for testing, the mock servers from `ansible_playtest` can be automatically made available within that environment. This allows tests to use features like the mock SMTP server without needing to install the entire package manually.

### How to Use

```python
from ansible_playbook_runner.environment import VirtualEnvironment

# Create a virtual environment with ansible_playtest installed
venv = VirtualEnvironment("/path/to/project", name="venv")
venv.create(install_playtest=True)  # This automatically makes mock servers available

# Now you can run commands that use the mock servers
result = venv.run_command(["-c", "from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer"])
```

Alternatively, you can use the legacy function:

```python
from ansible_playbook_runner.environment import create_virtual_environment

# Create a virtual environment with ansible_playtest installed
venv_path = create_virtual_environment("/path/to/temp_dir", install_playtest=True)
```

## How It Works

When `install_playtest=True` is specified:

1. The system attempts to find the `ansible_playtest` package source in several locations
2. If found, it installs the package in development mode (`-e`)
3. If not found, it tries to install the package from PyPI
4. As a fallback, it creates a minimal package structure with the essential mock components

This ensures that the mock servers and verifiers are always available in the virtual environment, regardless of how it was created.

## Advanced Usage

You can also create a virtual environment first and then install the `ansible_playtest` package separately:

```python
venv = VirtualEnvironment("/path/to/project")
venv.create()
venv.install_ansible_playtest()  # Install specifically the ansible_playtest package

# Install other packages as needed
venv.install_packages(["pytest", "ansible"])
```

## Best Practices

1. Always create a fresh virtual environment for each test run to ensure isolation
2. Use the `cleanup()` method to remove the virtual environment when tests are complete
3. If you need additional packages, install them after installing `ansible_playtest`
