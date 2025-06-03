"""
Integration tests for the project playbooks using scenario-based test framework
"""

import os
import yaml
import logging

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from ansible_playtest.core.playbook_runner import PlaybookRunner
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario
from ansible_playtest.core.scenario_factory import ScenarioFactory


# Define the project root directory
project_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 
    os.pardir, 
    os.pardir, 
    os.pardir
))


# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Container for test results"""
    success: bool
    errors: List[str] = None
    scenario_results: List[Dict[str, Any]] = None
    artifacts_path: Optional[str] = None


class AnsiblePlaybookTestRunner:
    """
    Main entry point for running Ansible playbook tests with scenarios.
    
    This class orchestrates the entire testing process:
    1. Sets up the test environment and mocks
    2. Runs the playbook using PlaybookRunner
    3. Verifies results using scenario assertions
    4. Returns the test results and handles cleanup
    """
    def __init__(self, playbook_path=None, scenario_path=None, inventory_path=None, extra_vars=None):
        self.playbook_path = playbook_path
        self.scenario_path = scenario_path
        self.inventory_path = inventory_path
        self.extra_vars = extra_vars or {}
        self.temp_dirs = []
        self.mock_modules = None
        self.playbook_runner = None
        self.scenario = None
        
    def setup(self):
        """Setup the test environment"""
        
        # Load scenario if provided
        if self.scenario_path:
            self.scenario = ScenarioFactory().load_scenario(self.scenario_path)
        else:
            raise ValueError("No scenario path provided for test")
            
        # Create the playbook runner
        self.playbook_runner = PlaybookRunner(
            scenario = self.scenario,
        )
        
        return self
        
    def run(self) -> TestResult:
        """Run the playbook and validate results"""
        if not self.playbook_runner:
            raise RuntimeError("Test runner not set up. Call setup() first.")
            
        try:
            # Run the playbook
            run_result = self.playbook_runner.run_playbook_with_scenario(
                self.playbook_path)
            
            # Store artifacts path for potential inspection
            artifacts_path = self.playbook_runner.artifacts_dir
            
            success = run_result.get('rc', 1) == 0
            errors = []
            
            if not success:
                errors.append(f"Playbook execution failed with rc={run_result.get('rc')}")
                errors.append(run_result.get('stderr', 'No error output available'))
            
            # Validate scenario expectations if playbook execution was successful
            scenario_results = []
            if success and self.scenario:
                verifications = self.scenario.verify(self.playbook_runner.artifacts_dir)
                scenario_results = verifications
                # If any verification failed, mark the test as failed
                if any(not v["result"] for v in verifications):
                    success = False
                    errors.extend([v["message"] for v in verifications if not v["result"]])
            
            return TestResult(
                success=success,
                errors=errors,
                scenario_results=scenario_results,
                artifacts_path=artifacts_path
            )
            
        except Exception as e:
            return TestResult(
                success=False,
                errors=[f"Test execution error: {str(e)}"],
                scenario_results=None
            )
    
    def cleanup(self):
        """Clean up after test execution"""
        if self.playbook_runner:
            self.playbook_runner.cleanup()

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

    def parametrize_scenarios(self):
        """
        Create test parameters from the discovered scenarios

        Returns:
            list: list of (playbook_path, scenario_path) for pytest parametrize
            list: list of test IDs for pytest parametrize
        """
        factory = ScenarioFactory()
        
        discovered_scenarios = factory.discover_scenarios()

        # Create test parameters
        test_params = [(p, s) for s, p, _ in discovered_scenarios]
        test_ids = [self.get_scenario_id(s, p) for s, p, _ in discovered_scenarios]

        return test_params, test_ids

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