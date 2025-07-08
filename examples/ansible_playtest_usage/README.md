# Ansible Scenario Testing Demo

This directory contains a complete example demonstrating how to use the Ansible Scenario Testing framework with a simple playbook.

## What's Included

- **Playbook**: A demo playbook that performs several common tasks:
  - Pings a server to check connectivity
  - Retrieves data from a public API (JSONPlaceholder)
  - Sends email notifications
  - Uses a custom module to process data

- **Custom Module**: A simple `custom_processor` module that simulates processing project data

- **Test Scenario**: A scenario file that defines mock responses and verification criteria

- **Runner Script**: A Python script to execute the test using the framework

## Directory Structure

```
demo/
  ├── inventory/         # Inventory files
  │   └── hosts.ini      # Simple inventory file
  ├── playbooks/         # Playbooks and modules
  │   ├── demo_playbook.yml        # Main demo playbook
  │   └── library/                 # Custom modules
  │       └── custom_processor.py  # Custom module for testing
  ├── scenarios/         # Test scenarios
  │   └── demo_scenario.yml        # Test scenario for the demo playbook
  └── run_demo.py        # Script to run the test
```

## How to Run

Make sure you've installed the Ansible Scenario Testing framework:

```bash
cd /home/viewnext/src/ANSIBLE_TOOLS/ansible-scenario-testing
pip install -e .
```

or

```bash
pip install ansible-playtest
```

Then run the demo:

```bash
cd /examples/demo
./run_demo.py
```

### Options

- `--no-smtp`: Disable the mock SMTP server
- `--keep-artifacts` or `-k`: Keep test artifacts for debugging

## What This Demo Shows

1. **Module Mocking**: The `custom_processor` module is mocked to return predefined values without actually executing
2. **SMTP Mocking**: Email sending is mocked using a built-in SMTP server
3. **Verification Strategies**:
   - **Module Call Count**: Verifies each module is called the expected number of times
   - **Parameter Validation**: Checks that modules are called with the expected parameters
   - **Call Sequence**: Ensures modules are called in the correct order

## Customizing This Demo

Feel free to modify the playbook, scenario, or test script to see how the framework reacts to different situations:

1. Change parameter values in the playbook to see validation failures
2. Add or remove tasks to see sequence verification failures
3. Modify the scenario to expect different parameters or call sequences
