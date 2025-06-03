
import pytest

@pytest.mark.keep_artifacts
def test_ansible_playbook(playbook_path, 
                          scenario_path, 
                          playbook_runner
                          ):
    """
    Main test function that runs an Ansible playbook with a scenario.
    
    This test demonstrates how to access the playbook runner's success property
    and execution details after the playbook has run.
    """
    # Access the success property directly
    assert playbook_runner.success, f"Playbook execution failed: {playbook_runner.execution_details}"
    
    # You can also access specific details from the execution_details dictionary
    print(f"Playbook success: {playbook_runner.execution_details['playbook_success']}")
    print(f"Verification passed: {playbook_runner.execution_details['verification_passed']}")
    

