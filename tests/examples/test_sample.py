# Example test with markers

import pytest

def test_ansible_playbook(playbook_path, 
                          scenario_path, 
                          playbook_runner, 
                          smtp_mock):
    """
    Main test function that runs an Ansible playbook with a scenario.
    
    This test is automatically parametrized by pytest_generate_tests to run
    all discovered playbook/scenario combinations.
    """
    # Assert phase
    assert playbook_runner.success, f"Playbook execution failed: {playbook_runner.errors}"
   
