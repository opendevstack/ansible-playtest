#!/usr/bin/env python3
"""
Example test showing how to use the playbook_runner fixture
"""
import os
import pytest


def test_basic_playbook_execution(playbook_runner):
    """
    This test demonstrates how to directly use the PlaybookRunner fixture
    to run and test an Ansible playbook with a specific scenario.
    """
    # Path to the example playbook and scenario
    playbook_path = os.path.join('playbooks', 'demo_playbook_01.yml')
    scenario_path = os.path.join('scenarios', 'demo_scenario_01.yml') 
    
    # Optional: Path to the inventory file
    inventory_path = os.path.join('inventory', 'hosts.ini')
    
    # Optional: Extra variables to pass to the playbook
    extra_vars = {'test_var': 'test_value'}
    
    # Run the playbook with the scenario
    success, result = playbook_runner.run_playbook_with_scenario(
        playbook_path=playbook_path,
        scenario_name=scenario_path,
        inventory_path=inventory_path,
        extra_vars=extra_vars,
        keep_mocks=False  # Set to True to keep mock files for debugging
    )
    
    # Assert that the playbook execution was successful
    assert success, f"Playbook execution failed: {result}"
    
    # You can also assert specific things about the result
    assert result['playbook_success'], "Playbook did not run successfully"
    assert result['verification_passed'], "Verification failed"


@pytest.mark.parametrize("playbook_name, scenario_name", [
    ('demo_playbook_01.yml', 'demo_scenario_01.yml'),
    ('demo_playbook_02.yml', 'demo_scenario_02.yml')
])
def test_parametrized_playbook_execution(playbook_runner, playbook_name, scenario_name):
    """
    This test demonstrates how to parameterize tests using the PlaybookRunner fixture
    to run multiple playbook/scenario combinations.
    """
    # Construct full paths
    playbook_path = os.path.join('playbooks', playbook_name)
    scenario_path = os.path.join('scenarios', scenario_name)
    inventory_path = os.path.join('inventory', 'hosts.ini')
    
    # Run the playbook with the scenario
    success, result = playbook_runner.run_playbook_with_scenario(
        playbook_path=playbook_path,
        scenario_name=scenario_path,
        inventory_path=inventory_path
    )
    
    # Assert that the playbook execution was successful
    assert success, f"Playbook {playbook_name} with scenario {scenario_name} failed: {result}"
