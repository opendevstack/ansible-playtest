"""
Example test using ansible-playtest framework to test Ansible playbooks.
This test demonstrates how to use the framework to run a scenario against a playbook with a given inventory.
"""
import os
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario
from ansible_playtest.core.test_runner import AnsiblePlaybookTestRunner

# Define paths relative to this file
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIOS_DIR = os.path.join(EXAMPLES_DIR, 'scenarios')
PLAYBOOKS_DIR = os.path.join(EXAMPLES_DIR, 'playbooks')
INVENTORY_PATH = os.path.join(EXAMPLES_DIR, 'inventory', 'hosts.ini')


def test_demo_scenario():
    """
    Runs the demo scenario against the demo playbook using the provided inventory.
    """
    scenario_file = os.path.join(SCENARIOS_DIR, 'demo_scenario_01.yml')
    playbook_file = os.path.join(PLAYBOOKS_DIR, 'demo_playbook.yml')

    AnsiblePlaybookTestRunner.setConfigDir(EXAMPLES_DIR)

    runner = AnsiblePlaybookTestRunner(
        scenario_path=scenario_file,
        playbook_path=playbook_file,
        inventory_path=INVENTORY_PATH,
    )
    result = runner.run()
    assert result.success, f"Scenario failed: {result.errors}"
