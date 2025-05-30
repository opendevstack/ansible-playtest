# Ansible Scenario Testing Framework - Installation Guide

This guide will walk you through the installation and setup of the Ansible Scenario Testing Framework.

## Prerequisites

- Python 3.6 or higher
- pip package manager
- Ansible 2.9 or higher

## Installation Options

### Option 1: Install from Source (Development Mode)

To install the library in development mode, which allows you to make changes to the code:

```bash
cd /home/viewnext/src/ANSIBLE_TOOLS/ansible-scenario-testing
pip install -e .
```

This will install the package in "editable" mode, meaning changes to the source code will be immediately available.

### Option 2: Build a Distribution Package

To build a distribution package that can be installed elsewhere:

```bash
cd /home/viewnext/src/ANSIBLE_TOOLS/ansible-scenario-testing
python setup.py sdist bdist_wheel
```

This will create distribution files in the `dist/` directory.

## Verifying Installation

To verify that the installation was successful, run the following Python code:

```python
from ansible_playtest.core.scenario import Scenario
from ansible_playtest.core.test_runner import AnsiblePlaybookTestRunner

print("Installation successful!")
```

## Running the Example

An example test script and scenario are included in the `examples/` directory:

```bash
cd ansible-scenario-testing
python examples/run_test.py path/to/your/playbook.yml --scenario examples/scenarios/example_scenario.yaml
```

## Integrating with Your Project

To integrate the framework with your existing project:

1. Import the necessary components:

```python
from ansible_playtest.core.runner import run_playbook_test
```

2. Create scenario files in your project's test directory

3. Run your tests:

```python
results = run_playbook_test(
    playbook_path='your_playbook.yml',
    scenario_path='your_scenario.yaml'
)
```

## Next Steps

- Review the documentation in the `docs/` directory
- Explore the example scenario in `examples/scenarios/`
- Create your own test scenarios

## Troubleshooting

If you encounter issues with the installation or usage:

1. Ensure you have the required Python version: `python --version`
2. Check that Ansible is installed: `ansible --version` 
3. Verify that aiosmtpd and other dependencies are installed: `pip list | grep aiosmtpd`
