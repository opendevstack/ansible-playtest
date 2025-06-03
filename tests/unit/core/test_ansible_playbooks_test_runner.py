"""
Unit tests for AnsiblePlaybookTestRunner class in ansible_playbooks_test_runner.py
"""
import os
import pytest
from unittest import mock
from ansible_playtest.core.ansible_playbooks_test_runner import AnsiblePlaybookTestRunner, TestResult

@pytest.fixture
def dummy_paths(tmp_path):
    playbook = tmp_path / 'dummy_playbook.yml'
    playbook.write_text('- hosts: all\n  tasks: []\n')
    scenario = tmp_path / 'dummy_scenario.yml'
    scenario.write_text('playbook: dummy_playbook.yml\n')
    return str(playbook), str(scenario)

def test_setup_and_run_success(dummy_paths):
    playbook_path, scenario_path = dummy_paths
    runner = AnsiblePlaybookTestRunner(playbook_path=playbook_path, scenario_path=scenario_path)
    # Patch AnsibleTestScenario and PlaybookRunner
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.AnsibleTestScenario') as MockScenario, \
         mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PlaybookRunner') as MockRunner:
        mock_scenario = MockScenario.from_yaml_file.return_value
        mock_scenario.verify.return_value = [{'result': True, 'message': 'ok'}]
        mock_runner = MockRunner.return_value
        mock_runner.run.return_value = {'rc': 0}
        mock_runner.artifacts_dir = '/tmp/artifacts'
        runner.setup()
        result = runner.run()
    assert isinstance(result, TestResult)
    assert result.success
    assert result.errors == []
    assert result.artifacts_path == '/tmp/artifacts'
    assert result.scenario_results == [{'result': True, 'message': 'ok'}]

def test_setup_no_scenario_path():
    runner = AnsiblePlaybookTestRunner(playbook_path='foo')
    with pytest.raises(ValueError):
        runner.setup()

def test_run_failure_on_playbook_error(dummy_paths):
    playbook_path, scenario_path = dummy_paths
    runner = AnsiblePlaybookTestRunner(playbook_path=playbook_path, scenario_path=scenario_path)
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.AnsibleTestScenario') as MockScenario, \
         mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PlaybookRunner') as MockRunner:
        mock_scenario = MockScenario.from_yaml_file.return_value
        mock_scenario.verify.return_value = [{'result': True, 'message': 'ok'}]
        mock_runner = MockRunner.return_value
        mock_runner.run.return_value = {'rc': 1, 'stderr': 'fail'}
        mock_runner.artifacts_dir = '/tmp/artifacts'
        runner.setup()
        result = runner.run()
    assert not result.success
    assert 'Playbook execution failed' in result.errors[0]
    assert result.artifacts_path == '/tmp/artifacts'

def test_run_verification_failure(dummy_paths):
    playbook_path, scenario_path = dummy_paths
    runner = AnsiblePlaybookTestRunner(playbook_path=playbook_path, scenario_path=scenario_path)
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.AnsibleTestScenario') as MockScenario, \
         mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PlaybookRunner') as MockRunner:
        mock_scenario = MockScenario.from_yaml_file.return_value
        mock_scenario.verify.return_value = [
            {'result': False, 'message': 'fail1'},
            {'result': True, 'message': 'ok'}
        ]
        mock_runner = MockRunner.return_value
        mock_runner.run.return_value = {'rc': 0}
        mock_runner.artifacts_dir = '/tmp/artifacts'
        runner.setup()
        result = runner.run()
    assert not result.success
    assert 'fail1' in result.errors
    assert result.artifacts_path == '/tmp/artifacts'
    assert result.scenario_results[0]['result'] is False

def test_run_exception_returns_failure(dummy_paths):
    playbook_path, scenario_path = dummy_paths
    runner = AnsiblePlaybookTestRunner(playbook_path=playbook_path, scenario_path=scenario_path)
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.AnsibleTestScenario') as MockScenario, \
         mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PlaybookRunner') as MockRunner:
        MockScenario.from_yaml_file.side_effect = Exception('boom')
        try:
            runner.setup()
        except Exception:
            pass
        result = runner.run()
    assert not result.success
    assert 'Test execution error' in result.errors[0]

def test_cleanup_calls_playbook_runner_cleanup(dummy_paths):
    playbook_path, scenario_path = dummy_paths
    runner = AnsiblePlaybookTestRunner(playbook_path=playbook_path, scenario_path=scenario_path)
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.AnsibleTestScenario') as MockScenario, \
         mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PlaybookRunner') as MockRunner:
        mock_runner = MockRunner.return_value
        runner.setup()
        runner.cleanup()
        mock_runner.cleanup.assert_called_once()

def test_get_scenario_id_and_parametrize_scenarios():
    runner = AnsiblePlaybookTestRunner()
    # Patch ScenarioFactory.discover_scenarios
    with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.ScenarioFactory') as MockFactory:
        MockFactory.return_value.discover_scenarios.return_value = [
            ('/path/to/scenario.yml', '/path/to/playbook.yml', 'scenario_id')
        ]
        # Patch SCENARIO_DIR and PLAYBOOKS_DIR
        with mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.SCENARIO_DIR', '/path/to'), \
             mock.patch('ansible_playtest.core.ansible_playbooks_test_runner.PLAYBOOKS_DIR', '/playbooks'):
            test_params, test_ids = runner.parametrize_scenarios()
            assert test_params == [('/path/to/playbook.yml', '/path/to/scenario.yml')]
            assert test_ids[0].endswith('::scenario_id')
