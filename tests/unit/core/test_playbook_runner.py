"""
Unit tests for PlaybookRunner class in playbook_runner.py
"""
import os
import tempfile
import pytest
from unittest import mock
from ansible_playtest.core.playbook_runner import PlaybookRunner

@pytest.fixture
def runner():
    return PlaybookRunner()

def test_get_mock_modules_path(runner):
    path = runner.get_mock_modules_path()
    assert path.endswith('mock_modules')
    assert os.path.isdir(os.path.dirname(path))

def test_copy_real_collections_to_temp_creates_dir(runner, tmp_path):
    temp_dir = str(tmp_path)
    # Create a fake collections dir in the project
    collections_dir = os.path.join(runner.project_dir, 'ansible_collections')
    os.makedirs(collections_dir, exist_ok=True)
    # Add a dummy collection
    dummy_collection = os.path.join(collections_dir, 'dummy')
    os.makedirs(dummy_collection, exist_ok=True)
    temp_collections_dir = runner.copy_real_collections_to_temp(temp_dir)
    assert os.path.exists(temp_collections_dir)
    assert os.path.exists(os.path.join(temp_collections_dir, 'dummy'))
    # Cleanup
    import shutil
    shutil.rmtree(collections_dir)

def test_overlay_mock_modules_copies_files(runner, tmp_path):
    temp_collections_dir = tmp_path / 'ansible_collections'
    temp_collections_dir.mkdir()
    # Create mock_collections/ansible_collections with a dummy file
    mock_collections_dir = os.path.join(runner.parent_dir, 'mock_collections', 'ansible_collections')
    os.makedirs(mock_collections_dir, exist_ok=True)
    dummy_file = os.path.join(mock_collections_dir, 'dummy.txt')
    with open(dummy_file, 'w') as f:
        f.write('test')
    runner.overlay_mock_modules(str(temp_collections_dir))
    # The dummy file should be copied
    found = False
    for root, _, files in os.walk(temp_collections_dir):
        if 'dummy.txt' in files:
            found = True
    assert found
    # Cleanup
    import shutil
    shutil.rmtree(os.path.join(runner.parent_dir, 'mock_collections'))

def test_run_playbook_with_scenario_playbook_not_found(runner):
    # Should return False and error if playbook does not exist
    success, result = runner.run_playbook_with_scenario('nonexistent_playbook.yml', 'dummy_scenario')
    assert not success
    assert 'error' in result

def test_run_playbook_with_scenario_scenario_not_found(runner, tmp_path):
    # Create a dummy playbook file
    playbook_path = tmp_path / 'dummy_playbook.yml'
    playbook_path.write_text('- hosts: all\n  tasks: []\n')
    # Patch load_scenario to raise FileNotFoundError
    with mock.patch('ansible_playtest.core.playbook_runner.load_scenario', side_effect=FileNotFoundError('not found')):
        success, result = runner.run_playbook_with_scenario(str(playbook_path), 'nonexistent_scenario')
    assert not success
    assert 'error' in result

def test_run_playbook_with_scenario_success_flow(runner, tmp_path):
    # Create a dummy playbook file
    playbook_path = tmp_path / 'dummy_playbook.yml'
    playbook_path.write_text('- hosts: all\n  tasks: []\n')
    # Patch load_scenario, ModuleMockManager, MockSMTPServer, ansible_runner.run
    dummy_scenario = mock.Mock()
    dummy_scenario.get_name.return_value = 'Test Scenario'
    dummy_scenario.get_description.return_value = 'desc'
    dummy_scenario.scenario_data = {'service_mocks': {}}
    dummy_scenario.run_verifiers.return_value = {'ver': True}
    dummy_scenario.verification_strategies = [mock.Mock(get_status=lambda: True)]
    dummy_scenario.expects_failure.return_value = False
    with mock.patch('ansible_playtest.core.playbook_runner.load_scenario', return_value=dummy_scenario), \
         mock.patch('ansible_playtest.core.playbook_runner.ModuleMockManager') as MockManager, \
         mock.patch('ansible_playtest.core.playbook_runner.ansible_runner.run') as mock_run:
        mock_manager = MockManager.return_value
        mock_manager.create_mock_configs.return_value = {}
        mock_manager.set_env_vars.return_value = os.environ.copy()
        mock_manager.module_temp_files = []
        mock_run.return_value.rc = 0
        success, result = runner.run_playbook_with_scenario(str(playbook_path), 'dummy_scenario')
    assert success
    assert result['success']
    assert result['playbook_success']
    assert result['verification_passed']
    assert result['expected_failure'] is False
    assert 'verification' in result
