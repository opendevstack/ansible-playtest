"""
Factory for loading Ansible test scenarios
"""
import os
import glob
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario

class ScenarioFactory:
    """
    Factory class for loading test scenarios based on different criteria.
    Provides methods to find, list, and load scenarios from the filesystem.
    """
    
    def __init__(self, config_dir=None):
        """
        Initialize the scenario factory with a configuration directory.
        
        Args:
            config_dir (str, optional): Custom configuration directory.
                If None, uses the default from AnsibleTestScenario.CONFIG_DIR.
        """
        # Use provided config_dir or get from AnsibleTestScenario
        if config_dir:
            self.config_dir = AnsibleTestScenario.set_config_dir(config_dir)
        else:
            self.config_dir = AnsibleTestScenario.CONFIG_DIR
            
        # Define the scenarios directory
        self.scenarios_dir = os.path.join(self.config_dir, 'scenarios')
        
    def load_scenario(self, scenario_name):
        """
        Load a test scenario by name (without file extension).
        
        The function searches for scenarios in the following order:
        1. If scenario_name is an absolute path, use it directly
        2. If scenario_name is a relative path from the current directory, use that
        3. Look in the configured scenarios directory and its subdirectories
        
        Args:
            scenario_name (str): Name of the scenario or path to scenario file
            
        Returns:
            AnsibleTestScenario: Loaded scenario object
            
        Raises:
            FileNotFoundError: If the scenario could not be found
        """
        # First check if the scenario_name is a valid file path
        if os.path.isfile(scenario_name):
            print(f"Found scenario at {scenario_name}")
            return AnsibleTestScenario(scenario_name)
        
        # Next check if scenario_name is a relative file path from current directory
        current_dir_scenario = os.path.join(os.getcwd(), scenario_name)
        if os.path.isfile(current_dir_scenario):
            print(f"Found scenario at {current_dir_scenario}")
            return AnsibleTestScenario(current_dir_scenario)
            
        # Then check if scenario_name contains a path separator
        if '/' in scenario_name:
            # If it has a path separator, treat as a relative path inside the scenarios directory
            scenario_path = os.path.join(self.scenarios_dir, f"{scenario_name}.yaml")
            if os.path.exists(scenario_path):
                print(f"Found scenario at {scenario_path}")
                return AnsibleTestScenario(scenario_path)
            
            # Try with .yml extension too
            yml_path = os.path.join(self.scenarios_dir, f"{scenario_name}.yml")
            if os.path.exists(yml_path):
                print(f"Found scenario at {yml_path}")
                return AnsibleTestScenario(yml_path)
        else:
            # Check if the scenario exists in the root scenarios directory
            scenario_path = os.path.join(self.scenarios_dir, f"{scenario_name}.yaml")
            if os.path.exists(scenario_path):
                print(f"Found scenario at {scenario_path}")
                return AnsibleTestScenario(scenario_path)
        
        # Look in subfolders for scenario files
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                file_path = os.path.join(root, file)
                base_name = os.path.splitext(file)[0]
                
                # Handle both the direct filename match and the case with path separator
                if (base_name == scenario_name or
                    file_path.endswith(f"{scenario_name}.yaml") or
                    file_path.endswith(f"{scenario_name}.yml")):
                    print(f"Found scenario at {file_path}")
                    return AnsibleTestScenario(file_path)
        
        # If we reach here, the scenario was not found
        raise FileNotFoundError(f"Scenario not found in {self.scenarios_dir}."
                               f"\nAvailable scenarios:{self.list_available_scenarios()}")
    
    def list_available_scenarios(self):
        """
        Get a list of all available scenario names.
        
        Returns:
            list: List of scenario names without file extensions
        """
        # Collect all scenario paths
        available_scenarios = []
        for root, _, files in os.walk(self.scenarios_dir):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    rel_path = os.path.relpath(os.path.join(root, file), self.scenarios_dir)
                    scenario_id = os.path.splitext(rel_path)[0]
                    available_scenarios.append(scenario_id)
        
        return available_scenarios
    
    def bulk_load_scenarios(self, pattern=None):
        """
        Load multiple scenarios matching a pattern.
        
        Args:
            pattern (str, optional): Glob pattern to match scenario names.
                If None, loads all available scenarios.
                
        Returns:
            dict: Dictionary mapping scenario names to loaded scenario objects
        """
        scenarios = {}
        
        if pattern:
            # Handle specific pattern matching
            matching_files = []
            for ext in ['.yaml', '.yml']:
                pattern_with_ext = f"{pattern}{ext}"
                # Check in root scenarios dir
                matching_files.extend(glob.glob(os.path.join(self.scenarios_dir, pattern_with_ext)))
                # Check in subdirectories
                matching_files.extend(glob.glob(os.path.join(self.scenarios_dir, '**', pattern_with_ext), recursive=True))
                
            for file_path in matching_files:
                try:
                    scenario = AnsibleTestScenario(file_path)
                    rel_path = os.path.relpath(file_path, self.scenarios_dir)
                    scenario_id = os.path.splitext(rel_path)[0]
                    scenarios[scenario_id] = scenario
                except Exception as e:
                    print(f"Error loading scenario {file_path}: {str(e)}")
        else:
            # Load all scenarios
            for scenario_name in self.list_available_scenarios():
                try:
                    scenarios[scenario_name] = self.load_scenario(scenario_name)
                except Exception as e:
                    print(f"Error loading scenario {scenario_name}: {str(e)}")
        
        return scenarios