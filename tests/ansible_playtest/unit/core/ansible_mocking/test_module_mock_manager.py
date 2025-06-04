"""
Unit tests for ModuleMockManager class in module_mock_manager.py
"""
import os
import json
import tempfile
import shutil
import pytest
from ansible_playtest.core.ansible_mocking.module_mock_manager import ModuleMockManager

class DummyScenario:
    def get_mock_response(self, module_name):
        return {'mocked': module_name}

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def test_create_mock_configs_creates_files(temp_dir):
    scenario = DummyScenario()
    manager = ModuleMockManager(temp_dir)
    module_names = ['foo.bar', 'baz']
    configs = manager.create_mock_configs(scenario, module_names)
    for module in module_names:
        file_path = configs[module]
        assert os.path.exists(file_path)
        with open(file_path) as f:
            data = json.load(f)
        assert data == {'mocked': module}
    assert set(configs.keys()) == set(module_names)
    assert set(manager.module_configs.keys()) == set(module_names)
    assert len(manager.module_temp_files) == len(module_names)

def test_set_env_vars_sets_expected_vars(temp_dir):
    scenario = DummyScenario()
    manager = ModuleMockManager(temp_dir)
    module_names = ['foo.bar', 'baz']
    manager.create_mock_configs(scenario, module_names)
    env = {}
    updated_env = manager.set_env_vars(env)
    for module in module_names:
        env_module = module.replace('.', '_').upper()
        assert updated_env[f'ANSIBLE_MOCK_{env_module}_CONFIG']
        assert updated_env[f'ANSIBLE_MOCK_{env_module}_ENABLED'] == 'true'

def test_cleanup_removes_files(temp_dir):
    scenario = DummyScenario()
    manager = ModuleMockManager(temp_dir)
    module_names = ['foo.bar', 'baz']
    configs = manager.create_mock_configs(scenario, module_names)
    # Files should exist
    for file_path in configs.values():
        assert os.path.exists(file_path)
    manager.cleanup()
    # Files should be removed
    for file_path in configs.values():
        assert not os.path.exists(file_path)
