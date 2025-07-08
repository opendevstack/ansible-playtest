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

When `install_playtest=True` is specified, the system uses a robust fallback mechanism:

1. **Development Mode Detection**: Attempts to find the `ansible_playtest` package source in several locations relative to the current file
2. **Project Root Installation**: If found, installs the package in development mode (`pip install -e`)
3. **PyPI Fallback**: If source not found, tries to install from PyPI using both `ansible-playtest` and `ansible_playtest` package names
4. **Graceful Degradation**: If all installation methods fail, logs a warning but continues (allowing manual installation later)

This multi-tier approach ensures that the mock servers and verifiers are available regardless of the deployment scenario - whether running from source, installed package, or development environment.

## Advanced Usage

You can also create a virtual environment first and then install the `ansible_playtest` package separately:

```python
venv = VirtualEnvironment("/path/to/project")
venv.create()
venv.install_ansible_playtest()  # Install specifically the ansible_playtest package

# Install other packages as needed
venv.install_packages(["pytest", "ansible"])

# Run commands in the virtual environment
result = venv.run_command(["-m", "pytest", "tests/"])

# Run shell commands with proper environment
result = venv.run_shell_command(["ansible-playbook", "playbook.yml"])

# Get environment variables for external tools
env_vars = venv.get_environment_vars({"CUSTOM_VAR": "value"})
```

## Available Methods

The `VirtualEnvironment` class provides the following key methods:

### Core Methods

- **`create(install_playtest=True)`**: Creates the virtual environment and optionally installs ansible_playtest
- **`cleanup()`**: Removes the virtual environment directory and all contents
- **`install_packages(packages)`**: Installs a list of packages using pip
- **`install_requirements(requirements_file)`**: Installs packages from a requirements.txt file
- **`install_ansible_playtest(src_dir=None)`**: Specifically installs the ansible_playtest package

### Command Execution

- **`run_command(command, env=None, capture_output=False, text=True, check=False)`**: Runs Python commands in the virtual environment
- **`run_shell_command(command, env=None, capture_output=False, text=True, check=False)`**: Runs shell commands with virtual environment activated
- **`get_environment_vars(additional_env=None)`**: Returns environment variables for external tool integration

### Properties

- **`path`**: Full path to the virtual environment directory
- **`python_path`**: Path to the virtual environment's Python executable
- **`pip_path`**: Path to the virtual environment's pip executable

## Best Practices

1. **Always create a fresh virtual environment for each test run** to ensure isolation
2. **Use the `cleanup()` method** to remove the virtual environment when tests are complete
3. **Install additional packages after creating the environment**: Install `ansible_playtest` first, then other dependencies
4. **Use `run_command()` for Python scripts** and `run_shell_command()` for direct shell commands
5. **Leverage `get_environment_vars()`** when integrating with external tools that need the virtual environment context
6. **Handle installation failures gracefully**: The `install_ansible_playtest()` method will attempt multiple installation strategies

## Integration with Test Scenarios

The virtual environment support integrates seamlessly with the test scenario framework. When running complex scenarios with multiple mock configurations, the virtual environment ensures all dependencies are properly isolated:

```python
# Example: Running a complex test scenario
venv = VirtualEnvironment("/tmp/test_env")
venv.create(install_playtest=True)

# Install additional test dependencies
venv.install_packages(["ansible", "requests"])

# Run the test scenario
result = venv.run_command([
    "-m", "pytest", 
    "tests/test_scenarios.py::test_myservice_integration",
    "-v"
])

# Clean up when done
venv.cleanup()
```

This approach ensures that complex scenarios with multiple service mocks run in complete isolation without affecting the host system.
