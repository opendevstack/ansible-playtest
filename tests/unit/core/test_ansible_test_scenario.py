"""
Unit tests for AnsibleTestScenario class in ansible_test_scenario.py
"""
import os
import tempfile
import shutil
import yaml
import json
import pytest
from unittest import mock
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario

@pytest.fixture
def temp_scenario_file(tmp_path):
    scenario_data = {
        'name': 'Test Scenario',
        'description': 'A scenario for testing.',
        'playbook': 'dummy_playbook.yml',
        'service_mocks': {
            'dummy_module': {'result': 'ok'}
        },
        'verify': {
            'expected_errors': [
                {'expect_process_failure': True}
            ]
        },
        'some_date': '${DATE:+1}',
        'today_macro': '${TODAY}'
    }
    scenario_file = tmp_path / 'test_scenario.yaml'
    with open(scenario_file, 'w') as f:
        yaml.safe_dump(scenario_data, f)
    return scenario_file

def test_load_scenario_and_macros(temp_scenario_file):
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    # Check name and description
    assert scenario.get_name() == 'Test Scenario'
    assert scenario.get_description() == 'A scenario for testing.'
    # Check date macro is replaced
    assert 'some_date' in scenario.scenario_data
    assert not scenario.scenario_data['some_date'].startswith('${DATE:')
    # Check TODAY macro is replaced
    assert 'today_macro' in scenario.scenario_data
    assert not scenario.scenario_data['today_macro'].startswith('${TODAY}')

def test_get_mock_response(temp_scenario_file):
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    # Should return the mock defined in service_mocks
    assert scenario.get_mock_response('dummy_module') == {'result': 'ok'}
    # Should return default for unknown module
    assert scenario.get_mock_response('unknown_module') == {'success': True}

def test_create_temp_file(temp_scenario_file):
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    module_name = 'dummy_module'
    with scenario.create_temp_file(module_name) as temp_file:
        assert os.path.exists(temp_file)
        with open(temp_file) as f:
            data = json.load(f)
        assert data == {'result': 'ok'}
    # File should be cleaned up
    assert not os.path.exists(temp_file)

def test_expects_failure(temp_scenario_file):
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    assert scenario.expects_failure() is True

def test_run_verifiers_calls_strategies(temp_scenario_file):
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    # Patch verification_strategies to mock
    mock_strategy = mock.Mock()
    mock_strategy.verify.return_value = {'result': 'verified'}
    scenario.verification_strategies = [mock_strategy]
    
    # Create dummy playbook statistics to pass to run_verifiers
    playbook_stats = {'stats': 1}
    results = scenario.run_verifiers(playbook_stats)
    
    assert results == {'result': 'verified'}
    mock_strategy.verify.assert_called_once_with(scenario.scenario_data, playbook_stats)

def test_playbook_path_resolution(temp_scenario_file):
    """Test the playbook path resolution from the scenario"""
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    # The scenario fixture has 'dummy_playbook.yml' as the playbook
    assert scenario.scenario_data['playbook'] == 'dummy_playbook.yml'

def test_temp_files_dir(temp_scenario_file):
    """Test that TEMP_FILES_DIR is correctly set and managed"""
    import tempfile
    
    # Verify the directory pattern is correct
    assert AnsibleTestScenario.TEMP_FILES_DIR.startswith(tempfile.gettempdir())
    assert 'ansible_test_' in AnsibleTestScenario.TEMP_FILES_DIR
    
    # Verify the directory gets created when instantiating a scenario
    scenario = AnsibleTestScenario(str(temp_scenario_file))
    assert os.path.exists(AnsibleTestScenario.TEMP_FILES_DIR)

def test_config_dir_setting():
    """Test the static config directory setting"""
    # Save original value to restore later
    original_config_dir = AnsibleTestScenario.CONFIG_DIR
    
    try:
        # Test with a valid directory (using /tmp which should exist on most systems)
        test_dir = tempfile.gettempdir()
        result = AnsibleTestScenario.set_config_dir(test_dir)
        assert result == test_dir
        assert AnsibleTestScenario.CONFIG_DIR == test_dir
        
        # Test with None/empty should raise an error if no environment variable
        original_env = os.environ.get('ANSIBLE_PLAYTEST_CONFIG_DIR')
        if 'ANSIBLE_PLAYTEST_CONFIG_DIR' in os.environ:
            del os.environ['ANSIBLE_PLAYTEST_CONFIG_DIR']
        
        with pytest.raises(ValueError, match="Config directory cannot be empty"):
            AnsibleTestScenario.set_config_dir(None)
            
        # Test with invalid directory
        with pytest.raises(ValueError, match="Invalid config directory"):
            AnsibleTestScenario.set_config_dir("/path/does/not/exist/hopefully")
            
        # Restore original env var if it existed
        if original_env:
            os.environ['ANSIBLE_PLAYTEST_CONFIG_DIR'] = original_env
    
    finally:
        # Restore original value
        AnsibleTestScenario.CONFIG_DIR = original_config_dir
