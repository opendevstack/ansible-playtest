"""
Integration tests for the project playbooks using scenario-based test framework
"""

import os
import yaml
import logging
import tempfile
import shutil
import pytest

# Add the project root to the Python path
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ansible_playtest.core.playbook_runner import PlaybookRunner
from ansible_playtest.core.ansible_test_scenario import load_scenario, AnsibleTestScenario

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnsiblePlaybookTestRunner:
    """
    Main class for running Ansible playbook tests with scenarios.
    This class handles setup, execution, and teardown of test runs.
    """

    # Path to the playbooks directory
    PLAYBOOKS_DIR = os.path.join(project_root, 'playbooks')

    # Path to the test inventory
    TEST_INVENTORY = os.path.join(project_root, 'tests', 'test_data', 'inventory.yaml')

    # Path to scenario directory
    SCENARIO_DIR = os.path.join(project_root, 'tests', 'test_data', 'scenarios')

    @classmethod
    def setConfigDir(cls, config_dir):
        """
        Set the configuration directory for scenarios.
        
        Args:
            config_dir (str): The path to the configuration directory
        """
        if config_dir and os.path.isdir(config_dir):
            cls.SCENARIO_DIR = os.path.abspath(config_dir)
            logger.info(f"Set scenario configuration directory to: {cls.SCENARIO_DIR}")
        else:
            logger.warning(f"Invalid config directory: {config_dir}. Using default: {cls.SCENARIO_DIR}")
        return cls.SCENARIO_DIR

    def __init__(self, playbook_path=None, scenario_path=None, inventory_path=None, 
                 extra_vars=None, keep_mocks=False, use_smtp_mock=True, smtp_port=1025):
        """
        Initialize the test runner with configuration
        
        Args:
            playbook_path: Path to the playbook to test
            scenario_path: Path to the scenario file or name of the scenario
            inventory_path: Path to the inventory file to use
            extra_vars: Dictionary of extra variables to pass to the playbook
            keep_mocks: Whether to keep mock files after execution
            use_smtp_mock: Whether to start a mock SMTP server during tests
            smtp_port: Port to use for the mock SMTP server
        """
        self.playbook_path = playbook_path
        self.scenario_path = scenario_path
        self.inventory_path = inventory_path
        self.extra_vars = extra_vars or {}
        self.keep_mocks = keep_mocks
        self.use_smtp_mock = use_smtp_mock
        self.smtp_port = smtp_port
        self.artifacts_dir = tempfile.mkdtemp(prefix="ansible_test_run_")
        self.scenario_instance = None
        
        logger.info("TestRunner configuration:")
        logger.info(f"Playbook path: {self.playbook_path}")
        logger.info(f"Scenario path: {self.scenario_path}")
        logger.info(f"Inventory path: {self.inventory_path}")
        logger.info(f"Extra variables: {self.extra_vars}")
        logger.info(f"Keep mocks: {self.keep_mocks}")
        logger.info(f"Use SMTP mock: {self.use_smtp_mock}")
        logger.info(f"SMTP port: {self.smtp_port}")
        logger.info(f"Artifacts directory: {self.artifacts_dir}")
        
    def setup(self):
        """Set up the test environment"""
        # Create artifacts directory if it doesn't exist
        os.makedirs(self.artifacts_dir, exist_ok=True)
        
        # Load the scenario if a path was provided
        if self.scenario_path:
            if isinstance(self.scenario_path, str):
                self.scenario_instance = load_scenario(self.scenario_path)
            elif isinstance(self.scenario_path, AnsibleTestScenario):
                self.scenario_instance = self.scenario_path
        
        return self
        
    def run(self):
        """Run the playbook with the scenario"""
        if not self.playbook_path:
            raise ValueError("No playbook path provided")
            
        if not self.scenario_instance and not self.scenario_path:
            raise ValueError("No scenario provided")
            
        # Make sure the scenario is loaded
        if not self.scenario_instance:
            self.setup()
        
        # Get the scenario name/ID
        scenario_id = self.scenario_path
        if isinstance(self.scenario_instance, AnsibleTestScenario):
            scenario_id = self.scenario_instance.get_name()
            
        # Run the playbook with the scenario
        runner = PlaybookRunner()
        success, result = runner.run_playbook_with_scenario(
            self.playbook_path,
            scenario_id,
            inventory_path=self.inventory_path,
            extra_vars=self.extra_vars,
            keep_mocks=self.keep_mocks,
            use_smtp_mock=self.use_smtp_mock,
            smtp_port=self.smtp_port
        )
        
        result['success'] = success
        return result
        
    def cleanup(self):
        """Clean up the test environment"""
        # Remove the artifacts directory
        if os.path.exists(self.artifacts_dir):
            shutil.rmtree(self.artifacts_dir)

    def get_playbook_path(self, playbook_name):
        """Get the full path to a playbook"""
        # If the playbook name already includes the path, use it as is
        if os.path.isabs(playbook_name) and os.path.exists(playbook_name):
            return playbook_name
            
        # Otherwise, look in the playbooks directory
        return os.path.join(PLAYBOOKS_DIR, playbook_name)

    def get_scenario_id(self, scenario_path, playbook):
        """Get a readable ID for the test case"""
        # Extract the relative path from the scenario directory
        rel_path = os.path.relpath(scenario_path, SCENARIO_DIR)
        scenario_id = os.path.splitext(rel_path)[0]
        playbook_base = os.path.basename(playbook)
        return f"{playbook_base}::{scenario_id}"

    def discover_scenarios(self):
        """
        Discover all scenario files and extract their playbook information
        
        Returns:
            list of tuples: (scenario_path, playbook_path, scenario_id)
        """
        logger.info(f"Discovering scenarios in: {SCENARIO_DIR}")
        scenarios = []
        
        if not os.path.exists(SCENARIO_DIR):
            logger.error(f"Scenario directory not found: {SCENARIO_DIR}")
            return scenarios
            
        for root, _, files in os.walk(SCENARIO_DIR):
            for file in files:
                if file.endswith(('.yaml', '.yml')):
                    scenario_path = os.path.join(root, file)
                    try:
                        # Load the scenario to get the playbook
                        with open(scenario_path, 'r') as f:
                            scenario_data = yaml.safe_load(f)
                        
                        # Check if the scenario has a playbook field
                        if 'playbook' not in scenario_data:
                            logger.warning(f"Scenario {scenario_path} is missing 'playbook' field")
                            continue
                            
                        playbook_name = scenario_data['playbook']
                        playbook_path = get_playbook_path(playbook_name)
                        
                        # Skip if the playbook doesn't exist
                        if not os.path.exists(playbook_path):
                            logger.warning(f"Playbook {playbook_path} not found for scenario {scenario_path}")
                            continue
                            
                        # Get the relative scenario path for identification
                        rel_path = os.path.relpath(scenario_path, SCENARIO_DIR)
                        scenario_id = os.path.splitext(rel_path)[0]
                        
                        logger.info(f"Found scenario: {scenario_id} using playbook: {playbook_name}")
                        scenarios.append((scenario_path, playbook_path, scenario_id))
                            
                    except Exception as e:
                        logger.error(f"Error processing scenario {scenario_path}: {str(e)}")
                        
        return scenarios

    def parametrize_scenarios(self):
        """
        Create test parameters from the discovered scenarios
        
        Returns:
            list: list of (playbook_path, scenario_path) for pytest parametrize
            list: list of test IDs for pytest parametrize
        """
        discovered_scenarios = discover_scenarios()
        
        # Create test parameters
        test_params = [(p, s) for s, p, _ in discovered_scenarios]
        test_ids = [get_scenario_id(s, p) for s, p, _ in discovered_scenarios]
        
        return test_params, test_ids

# Generate test parameters
#test_params, test_ids = parametrize_scenarios()

    #@pytest.mark.parametrize("playbook_path,scenario_path", test_params, ids=test_ids)
    def test_playbook_with_scenario(self, playbook_path, scenario_path):
        """Test a playbook with a specific scenario"""
        # Verify the playbook file exists
        assert os.path.exists(playbook_path), f"Playbook file not found: {playbook_path}"
        
        # Get the scenario ID from the path
        rel_path = os.path.relpath(scenario_path, SCENARIO_DIR)
        scenario_id = os.path.splitext(rel_path)[0]
        
        # Log the test being run
        logger.info(f"Testing playbook '{os.path.basename(playbook_path)}' with scenario '{scenario_id}'")
        
        # Run the playbook with the scenario
        success, result = run_playbook_with_scenario(
            playbook_path, 
            scenario_id,
            inventory_path=TEST_INVENTORY
        )
        
        # Log detailed results
        logger.info(f"Playbook execution result: {'SUCCESS' if success else 'FAILURE'}")
        logger.info(f"Return code: {result.get('returncode')}")
        
        # Check the overall result which combines playbook execution success and verification success
        assert result.get('success', False), (
            f"Test failed: Playbook execution success={success}, "
            f"verification failures in {result.get('verification', {})}"
        )