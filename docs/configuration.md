# Configuration Options

This document describes the various configuration options available in the Ansible PlayTest framework.

## Scenario Configuration Directory

The scenario configuration directory is where the framework looks for test scenarios and related data. You can specify this directory in three ways:

### 1. Using the Command Line Interface

When using the CLI tool, you can specify the config directory using the `--config-dir` option:

```bash
ansible-playtest path/to/playbook.yml --scenario my_scenario --config-dir /path/to/my/config
```

### 2. Using an Environment Variable

You can set the `ANSIBLE_PLAYTEST_CONFIG_DIR` environment variable:

```bash
export ANSIBLE_PLAYTEST_CONFIG_DIR="/path/to/my/config"
ansible-playtest path/to/playbook.yml --scenario my_scenario
```

### 3. Programmatically in Python Code

When using the framework in your own Python code, you can use the `set_config_dir` class method:

```python
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario

# Set the config directory
AnsibleTestScenario.set_config_dir('/path/to/my/config')

# Now load scenarios or run tests
# ...
```

### Default Configuration

If no configuration directory is specified, the framework uses a default directory within the package, typically:
`<package_install_path>/ansible_playtest/tests/test_data`

### Directory Structure

Within the configuration directory, scenarios are expected to be in a `scenarios` subdirectory:

```
config_dir/
├── scenarios/
│   ├── scenario1.yaml
│   ├── scenario2.yml
│   └── subdir/
│       └── scenario3.yaml
└── other_test_data/
```

## Other Configuration Options

- **SMTP Server**: Configure using `--smtp-port` or disable with `--no-smtp`
- **Debugging**: Keep mock files after execution with `--keep-mocks`
