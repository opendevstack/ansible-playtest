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
    with mock.patch.object(scenario, 'playbook_statistics', return_value={'stats': 1}):
        results = scenario.run_verifiers()
    assert results == {'result': 'verified'}
    mock_strategy.verify.assert_called_once()

def test_get_summary_data_and_playbook_statistics(temp_scenario_file, tmp_path):
    # Create a dummy playbook_statistics.json in the expected location
    # The expected location is one directory up from ansible_test_scenario.py, i.e., src/ansible_playtest/playbook_statistics.json
    core_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up to src/ansible_playtest
    ansible_playtest_dir = os.path.abspath(os.path.join(core_dir, '../../../', 'src/ansible_playtest'))
    summary_file = os.path.join(ansible_playtest_dir, 'playbook_statistics.json')
    dummy_data = {'calls': 2}
    with open(summary_file, 'w') as f:
        json.dump(dummy_data, f)
    scenario = AnsibleTestScenario(temp_scenario_file)
    assert scenario.get_summary_data() == dummy_data
    assert scenario.playbook_statistics() == dummy_data
    os.remove(summary_file)
