"""
Example conftest.py for users of the library
"""
import pytest
import os

# Define paths relative to your project
PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), '../playbooks')
SCENARIOS_DIR = os.path.join(os.path.dirname(__file__), 'scenarios')

def pytest_configure(config):
    """Set default directories if not specified on command line"""
    if config.getoption("--ansible-playtest-playbook-dir") is None:
        config.option.ansible_playtest_playbook_dir = PLAYBOOKS_DIR
    
    if config.getoption("--ansible-playtest-scenarios-dir") is None:
        config.option.ansible_playtest_scenarios_dir = SCENARIOS_DIR