"""
Unit tests for ScenarioFactory class in scenario_factory.py
"""
import os
import tempfile
import shutil
import yaml
import pytest
from ansible_playtest.core.scenario_factory import ScenarioFactory
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario

class DummyScenario(AnsibleTestScenario):
    def __init__(self, path):
        self.path = path

@pytest.fixture
def temp_scenarios_dir(tmp_path):
    scenarios_dir = tmp_path / "scenarios"
    playbooks_dir = tmp_path / "playbooks"
    scenarios_dir.mkdir()
    playbooks_dir.mkdir()
    # Create a valid scenario file
    scenario_path = scenarios_dir / "test_scenario.yaml"
    playbook_path = playbooks_dir / "test_playbook.yml"
    scenario_data = {"playbook": "test_playbook.yml"}
    with open(scenario_path, "w") as f:
        yaml.safe_dump(scenario_data, f)
    with open(playbook_path, "w") as f:
        f.write("- hosts: all\n  tasks: []\n")
    return tmp_path

def test_list_available_scenarios(temp_scenarios_dir, monkeypatch):
    factory = ScenarioFactory(config_dir=str(temp_scenarios_dir))
    scenarios = factory.list_available_scenarios()
    assert "test_scenario" in scenarios

def test_load_scenario_by_name(temp_scenarios_dir, monkeypatch):
    factory = ScenarioFactory(config_dir=str(temp_scenarios_dir))
    scenario = factory.load_scenario("test_scenario", config_dir=str(temp_scenarios_dir))
    assert isinstance(scenario, AnsibleTestScenario)
    assert os.path.basename(scenario.scenario_path) == "test_scenario.yaml"

def test_load_scenario_by_path(temp_scenarios_dir):
    factory = ScenarioFactory(config_dir=str(temp_scenarios_dir))
    scenario_path = os.path.join(temp_scenarios_dir, "scenarios", "test_scenario.yaml")
    scenario = factory.load_scenario(scenario_path)
    assert isinstance(scenario, AnsibleTestScenario)
    assert scenario.scenario_path == scenario_path

def test_discover_scenarios(temp_scenarios_dir):
    factory = ScenarioFactory(config_dir=str(temp_scenarios_dir))
    scenarios = factory.discover_scenarios()
    assert len(scenarios) == 1
    scenario_path, playbook_path, scenario_id = scenarios[0]
    assert scenario_id == "test_playbook/test_scenario"
    assert scenario_path.endswith("test_scenario.yaml")
    assert playbook_path.endswith("test_playbook.yml")

def test_load_scenario_not_found(temp_scenarios_dir):
    factory = ScenarioFactory(config_dir=str(temp_scenarios_dir))
    with pytest.raises(FileNotFoundError):
        factory.load_scenario("nonexistent_scenario")
