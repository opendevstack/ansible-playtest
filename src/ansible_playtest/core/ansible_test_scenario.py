"""
Test framework for Ansible playbooks using scenario-based mocking
"""
import os
import yaml
import json
import tempfile
import uuid
from contextlib import contextmanager
import datetime
import re
from ansible_playtest.verifiers import VerificationStrategyFactory

class AnsibleTestScenario:
    """Class for loading and managing test scenarios"""
    
    # Static variable to store the configuration directory
    _DEFAULT_CONFIG_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'test_data'))
    CONFIG_DIR = os.environ.get('ANSIBLE_PLAYTEST_CONFIG_DIR', _DEFAULT_CONFIG_DIR)
    
    # Static variable to store the temporary files directory - using a single UUID for the entire class
    _temp_dir_uuid = uuid.uuid4().hex
    TEMP_FILES_DIR = os.path.join(tempfile.gettempdir(), f"ansible_test_{_temp_dir_uuid}")
    
    @classmethod
    def set_config_dir(cls, config_dir):
        """
        Set the configuration directory for scenarios.
        
        Args:
            config_dir (str): The path to the configuration directory
        
        Returns:
            str: The updated configuration directory path
        """
        if config_dir and os.path.isdir(config_dir):
            cls.CONFIG_DIR = os.path.abspath(config_dir)
            print(f"Set scenario configuration directory to: {cls.CONFIG_DIR}")
        else:
            print(f"Warning: Invalid config directory: {config_dir}. Using default: {cls.CONFIG_DIR}")
        return cls.CONFIG_DIR
    
    def __init__(self, scenario_path):
        """Initialize with a scenario YAML file"""
        self.scenario_path = scenario_path
        self.scenario_data = self._load_scenario()
        self.temp_files = {}
        
        # Create verification strategies based on scenario configuration
        self.verification_strategies = VerificationStrategyFactory.create_strategies(self.scenario_data)
        
        # Ensure temp directory exists
        os.makedirs(self.TEMP_FILES_DIR, exist_ok=True)
        
    def _load_scenario(self):
        """Load the scenario from YAML file"""
        with open(self.scenario_path, 'r') as f:
            scenario = yaml.safe_load(f)
            
        # Process date macros in the scenario
        return self._process_date_macros(scenario)
        
    def _process_date_macros(self, obj):
        """Process date macros in the scenario data recursively"""
        if isinstance(obj, dict):
            return {k: self._process_date_macros(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._process_date_macros(item) for item in obj]
        elif isinstance(obj, str):
            return self._replace_date_macros(obj)
        else:
            return obj
            
    def _replace_date_macros(self, text):
        """Replace date macros in a string with actual dates"""
        if not isinstance(text, str):
            return text
            
        # Define the date macro pattern: ${DATE:+/-days}
        pattern = r'\${DATE:([+-]\d+)}'
        
        def replace_date(match):
            days_offset = int(match.group(1))
            date = datetime.datetime.now() + datetime.timedelta(days=days_offset)
            return date.strftime('%Y-%m-%d %H:%M:%S')
            
        # Replace all occurrences
        result = re.sub(pattern, replace_date, text)
        
        # Handle special case for TODAY macro
        if '${TODAY}' in result:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            result = result.replace('${TODAY}', today)
            
        return result
    
    def get_mock_response(self, module_name, **kwargs):
        """Get the mock response for a module based on scenario"""
        if module_name in self.scenario_data.get('service_mocks', {}):
            return self.scenario_data['service_mocks'][module_name]        
            
        # Default fallback if no specific mock defined
        return {"success": True}
    
    @contextmanager
    def create_temp_file(self, module_name, content=None):
        """Create a temporary file for the module to read its config from"""
        file_path = None
        try:
            # Make sure the temp directory exists
            os.makedirs(AnsibleTestScenario.TEMP_FILES_DIR, exist_ok=True)
            
            # Create the temporary file with the mock configuration
            file_path = os.path.join(AnsibleTestScenario.TEMP_FILES_DIR, f"{module_name}_mock_config.json")
            
            # If content provided, use it; otherwise, use scenario mock data
            if content is None:
                mock_data = self.get_mock_response(module_name)
            else:
                mock_data = content
                
            # Write the mock configuration to the temp file
            with open(file_path, 'w') as f:
                json.dump(mock_data, f)
            
            self.temp_files[module_name] = file_path
            yield file_path
            
        finally:
            # Clean up the temporary file when done
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except (IOError, OSError):
                    pass

    def run_verifiers(self):
        """
        Verify scenario expectations using registered verification strategies
        
        Returns:
            dict: Combined verification results from all strategies
        """
        # Load module call statistics from the file generated by mock_module_tracker.py
        playbook_stats = self.playbook_statistics()
        
        # Combined results from all verification strategies
        combined_results = {}
        
        # Run each verification strategy
        for strategy in self.verification_strategies:
            results = strategy.verify(self.scenario_data, playbook_stats)
            # Merge results
            combined_results.update(results)
        
        return combined_results
        
    def get_name(self):
        """Get the scenario name"""
        return self.scenario_data.get('name', 'Unnamed Scenario')
        
    def get_description(self):
        """Get the scenario description"""
        return self.scenario_data.get('description', '')
        
    def expects_failure(self):
        """
        Check if this scenario expects the playbook to fail
        
        Returns:
            bool: True if the scenario expects the playbook to fail, False otherwise
        """
        # Check if any errors are configured with expect_process_failure: true
        if 'verify' in self.scenario_data and 'expected_errors' in self.scenario_data['verify']:
            expected_errors = self.scenario_data['verify']['expected_errors']
            for error in expected_errors:
                if error.get('expect_process_failure', False):
                    return True
        return False

    def get_summary_data(self):
        """Read playbook statistics from the playbook_statistics.json file"""
        summary_file = {}
        
        # Define the path to the playbook_statistics.json file
        # Look up one directory from the current file to the project root
        project_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
        summary_file = os.path.join(project_dir, 'playbook_statistics.json')
        
        try:
            # Check if the summary file exists
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
                return summary_data
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading module call statistics: {str(e)}")
            
        return {}

    def playbook_statistics(self):
        """Get the playbook statistics from the summary data file"""
        return self.get_summary_data()

def load_scenario(scenario_name):
    """
    Load a test scenario by name (without file extension).
    
    This is a convenience wrapper around ScenarioFactory.load_scenario.
    
    Args:
        scenario_name (str): Name of the scenario or path to scenario file
        
    Returns:
        AnsibleTestScenario: Loaded scenario object
        
    Raises:
        FileNotFoundError: If the scenario could not be found
    """
    from ansible_playtest.core.scenario_factory import ScenarioFactory
    
    factory = ScenarioFactory()
    print(f"Looking for scenario '{scenario_name}' in {factory.scenarios_dir}")
    
    try:
        return factory.load_scenario(scenario_name)
    except FileNotFoundError as e:
        print(f"ERROR: {str(e)}")
        print("Available scenarios:")
        
        # Print available scenarios
        for scenario in sorted(factory.list_available_scenarios()):
            print(f"  - {scenario}")
            
        raise FileNotFoundError(f"Scenario '{scenario_name}' not found.")