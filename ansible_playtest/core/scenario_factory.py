"""
Factory for loading Ansible test scenarios
"""
import os
import yaml
import logging
from typing import Optional, List, Tuple
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario

class ScenarioFactory:
    """
    Factory class for loading test scenarios based on different criteria.
    Provides methods to find, list, and load scenarios from the filesystem.

    Args:
        config_dir (Optional[str]): Root configuration directory. If provided,
            playbooks and scenarios will be located as subdirectories.
        scenarios_dir (Optional[str]): Directory where scenarios are located.
            If provided, overrides the default scenarios directory.
    """

    def __init__(self, 
                 config_dir: Optional[str] = None, 
                 scenarios_dir: Optional[str] = None,
                 playbooks_dir: Optional[str] = None):
        """
        Initialize the scenario factory with configuration and/or scenarios directory.

        Args:
            config_dir (Optional[str]): Root configuration directory.
            scenarios_dir (Optional[str]): Directory for scenario files.
            playbooks_dir (Optional[str]): Directory for playbook files.
        """
        # Initialize config_dir first before using it
        self.config_dir = os.path.abspath(config_dir) if config_dir else os.getcwd()

        if scenarios_dir:
            self.scenarios_dir = os.path.abspath(scenarios_dir)
        else:
            self.scenarios_dir = os.path.join(self.config_dir, 'scenarios')

        if playbooks_dir:
            self.playbooks_dir = os.path.abspath(playbooks_dir)
        else:
            self.playbooks_dir = os.path.join(self.config_dir, 'playbooks')
        
    @staticmethod
    def load_scenario(scenario_name, config_dir=None, scenarios_dir=None, playbooks_dir=None):
        """
        Static method to load a test scenario by name.
        This allows ScenarioFactory.load_scenario() to be called without instantiation.

        Args:
            scenario_name (str): Name of the scenario or path to scenario file
            config_dir (Optional[str]): Root configuration directory.
            scenarios_dir (Optional[str]): Directory for scenario files.
            playbooks_dir (Optional[str]): Directory for playbook files.

        Returns:
            AnsibleTestScenario: Loaded scenario object

        Raises:
            FileNotFoundError: If the scenario could not be found
        """
        factory = ScenarioFactory(config_dir=config_dir, scenarios_dir=scenarios_dir, playbooks_dir=playbooks_dir)
        return factory.load_scenario_instance(scenario_name)
        
    def load_scenario_instance(self, scenario_name):
        """
        Load a test scenario by name (without file extension).
        Instance method used by the static load_scenario method.

        Args:
            scenario_name (str): Name of the scenario or path to scenario file

        Returns:
            AnsibleTestScenario: Loaded scenario object

        Raises:
            FileNotFoundError: If the scenario could not be found
        """
        # First check if the scenario_name is a valid file path
        if os.path.isfile(scenario_name):
            return AnsibleTestScenario(scenario_name)
        
        # Next check if scenario_name is a relative file path from current directory
        current_dir_scenario = os.path.join(os.getcwd(), scenario_name)
        if os.path.isfile(current_dir_scenario):
            return AnsibleTestScenario(current_dir_scenario)
            
        # Relative to scenarios_dir
        for ext in ('.yaml', '.yml'):
            scenario_path = os.path.join(self.scenarios_dir, f"{scenario_name}{ext}")
            if os.path.isfile(scenario_path):
                return AnsibleTestScenario(scenario_path)

        # Search recursively in scenarios_dir
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    base_name = os.path.splitext(file)[0]
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.scenarios_dir)
                    rel_base = os.path.splitext(rel_path)[0]
                    if base_name == scenario_name or rel_base == scenario_name:
                        return AnsibleTestScenario(file_path)

        raise FileNotFoundError(
            f"Scenario '{scenario_name}' not found in {self.scenarios_dir}.\n"
            f"Available scenarios: {self.list_available_scenarios()}"
        )
    
    def list_available_scenarios(self) -> List[str]:
        """
        Get a list of all available scenario names.

        Returns:
            List[str]: List of scenario names without file extensions
        """
        available_scenarios = []
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.scenarios_dir)
                    scenario_id = os.path.splitext(rel_path)[0]
                    available_scenarios.append(scenario_id)
        return available_scenarios
    
    def discover_scenarios(self) -> List[Tuple[str, str, str]]:
        """
        Discover all scenario files and extract their playbook information.

        Returns:
            List[Tuple[str, str, str]]: (scenario_path, playbook_path, scenario_id)
        """
        logger = logging.getLogger(__name__)
        scenarios: List[Tuple[str, str, str]] = []

        if not os.path.exists(self.scenarios_dir):
            logger.error(f"Scenario directory not found: {self.scenarios_dir}")
            return scenarios

        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    scenario_path = os.path.join(root, file)
                    try:
                        with open(scenario_path, 'r', encoding='utf-8') as f:
                            scenario_data = yaml.safe_load(f)
                        if not scenario_data or 'playbook' not in scenario_data:
                            logger.warning(
                                f"Scenario {scenario_path} is missing 'playbook' field"
                            )
                            continue
                        playbook_name = scenario_data['playbook']

                        # Validate playbook existence using playbooks_dir if not absolute
                        if os.path.isabs(playbook_name):
                            playbook_path = playbook_name
                        else:
                            playbook_path = os.path.join(self.playbooks_dir, playbook_name)

                        if not os.path.exists(playbook_path):
                            logger.warning(
                                f"Playbook {playbook_path} not found for scenario {scenario_path}"
                            )
                            continue

                        rel_path = os.path.relpath(scenario_path, self.scenarios_dir)
                        # scenario_id: playbook + folder + scenario file name
                        scenario_folder = os.path.dirname(rel_path)
                        scenario_file = os.path.splitext(os.path.basename(rel_path))[0]
                        playbook_base = os.path.splitext(os.path.basename(playbook_name))[0]
                        if scenario_folder:
                            scenario_id = f"{playbook_base}/{scenario_folder}/{scenario_file}"
                        else:
                            scenario_id = f"{playbook_base}/{scenario_file}"
                        logger.info(
                            f"Found scenario: {scenario_id} using playbook: {playbook_path}"
                        )
                        scenarios.append((scenario_path, playbook_path, scenario_id))
                    except Exception as e:
                        logger.error(
                            f"Error processing scenario {scenario_path}: {str(e)}"
                        )
        return scenarios

