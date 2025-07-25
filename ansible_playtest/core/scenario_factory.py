"""
Factory for loading Ansible test scenarios
"""

import os
from typing import Optional, List, Tuple
import yaml
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario
from ansible_playtest.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


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

    def __init__(
        self,
        config_dir: Optional[str] = None,
        scenarios_dir: Optional[str] = None,
        playbooks_dir: Optional[str] = None,
    ):
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
            self.scenarios_dir = os.path.join(self.config_dir, "scenarios")

        if playbooks_dir:
            self.playbooks_dir = os.path.abspath(playbooks_dir)
        else:
            self.playbooks_dir = os.path.join(self.config_dir, "playbooks")

    @staticmethod
    def load_scenario(
        scenario_name, config_dir=None, scenarios_dir=None, playbooks_dir=None
    ):
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
        factory = ScenarioFactory(
            config_dir=config_dir,
            scenarios_dir=scenarios_dir,
            playbooks_dir=playbooks_dir,
        )
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
        for ext in (".yaml", ".yml"):
            scenario_path = os.path.join(self.scenarios_dir, f"{scenario_name}{ext}")
            if os.path.isfile(scenario_path):
                return AnsibleTestScenario(scenario_path)

        # Search recursively in scenarios_dir
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
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
                if file.endswith((".yaml", ".yml")):
                    rel_path = os.path.relpath(
                        os.path.join(root, file), self.scenarios_dir
                    )
                    scenario_id = os.path.splitext(rel_path)[0]
                    available_scenarios.append(scenario_id)
        return available_scenarios
    
    def _process_scenario_file(self, scenario_path: str, rel_path_source: Optional[str] = None) -> List[Tuple[str, str, str]]:
        """
        Process a single scenario file and extract its playbook information.
        
        Args:
            scenario_path (str): Path to the scenario file
            rel_path_source (Optional[str]): Source directory for calculating relative path.
                                           If None, self.scenarios_dir will be used.
                
        Returns:
            List[Tuple[str, str, str]]: List containing a single tuple of 
                                        (scenario_path, playbook_path, scenario_id) if successful,
                                        empty list otherwise
        """
        if not scenario_path.endswith((".yaml", ".yml")):
            logger.warning(
                "Provided scenario file %s is not a YAML file (.yaml, .yml)",
                scenario_path,
            )
            return []
            
        scenarios = []
        try:
            with open(scenario_path, "r", encoding="utf-8") as f:
                scenario_data = yaml.safe_load(f)
            
            if not scenario_data or "playbook" not in scenario_data:
                logger.warning(
                    "Scenario %s is missing 'playbook' field",
                    scenario_path,
                )
                return []
                
            playbook_name = scenario_data["playbook"]

            # Validate playbook existence using playbooks_dir if not absolute
            if os.path.isabs(playbook_name):
                playbook_path = playbook_name
            else:
                playbook_path = os.path.join(
                    self.playbooks_dir, playbook_name
                )

            if not os.path.exists(playbook_path):
                logger.warning(
                    "Playbook %s not found for scenario %s",
                    playbook_path,
                    scenario_path,
                )
                return []

            # Calculate relative path or use filename depending on context
            if rel_path_source:
                rel_path = os.path.relpath(scenario_path, rel_path_source)
            else:
                rel_path = os.path.basename(scenario_path)
                
            scenarios.append((scenario_path, playbook_path, f"{playbook_name}--{rel_path}"))
            
        except (IOError, yaml.YAMLError) as e:
            logger.error(
                "Error processing scenario %s: %s", scenario_path, str(e)
            )
            
        return scenarios

    def discover_scenarios(self) -> List[Tuple[str, str, str]]:
        """
        Discover all scenario files and extract their playbook information.
        If scenarios_dir is a file, it will only discover that specific scenario file.

        Returns:
            List[Tuple[str, str, str]]: (scenario_path, playbook_path, scenario_id)
        """
        scenarios: List[Tuple[str, str, str]] = []

        if not os.path.exists(self.scenarios_dir):
            logger.error("Path provided does not exist: %s", self.scenarios_dir)
            return scenarios

        # Check if scenarios_dir is a file (direct scenario file)
        if os.path.isfile(self.scenarios_dir):
            return self._process_scenario_file(self.scenarios_dir)

        if not os.path.isdir(self.scenarios_dir):
            logger.error("Scenario path %s exists but is not a directory or valid scenario file", self.scenarios_dir)
            return scenarios

        # Directory-based discovery
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith((".yaml", ".yml")):
                    scenario_path = os.path.join(root, file)
                    scenarios.extend(self._process_scenario_file(scenario_path, self.scenarios_dir))
                    
        return sorted(scenarios)
