#!/usr/bin/env python3

"""
Test runner for scenario-based playbook testing
"""

import os
import sys
import argparse
import tempfile
import json
import uuid
import ansible_runner
import shutil
from ansible_playtest.core.scenario_factory import ScenarioFactory

# Add the parent directory to path
parent_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(parent_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from ansible_playtest.core.ansible_mocking.module_mock_manager import ModuleMockManager


class PlaybookRunner:
    """Class for running Ansible playbooks with scenario-based testing"""
    
    def __init__(self, scenario=None):
        """Initialize the PlaybookRunner class"""
        self.scenario = scenario
        self.parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_dir = os.path.dirname(self.parent_dir)
        self.temp_dir = None
        self.temp_collections_dir = None
        self.module_temp_files = []
        self.module_mock_manager = None
        # Initialize properties to store execution results
        self.success = False
        self.execution_details = {}
        
    def get_mock_modules_path(self):
        """Get the path to mock modules directory"""
        return os.path.join(self.parent_dir, 'mock_modules')
    
    def copy_real_collections_to_temp(self, temp_dir):
        """
        Copy real collections to a temporary folder
        
        Args:
            temp_dir: Path to the temporary directory
            
        Returns:
            str: Path to the temporary collections directory
        """
        # Create temporary collections directory structure
        temp_collections_dir = os.path.join(temp_dir, 'ansible_collections')
        os.makedirs(temp_collections_dir, exist_ok=True)
        
        # Get paths to the real collections
        project_collections_dir = os.path.join(self.project_dir, 'ansible_collections')
        
        if os.path.exists(project_collections_dir):
            print(f"Copying collections from {project_collections_dir} to {temp_collections_dir}")
            # Use shutil.copytree for each subdirectory to preserve the structure
            for item in os.listdir(project_collections_dir):
                item_path = os.path.join(project_collections_dir, item)
                if os.path.isdir(item_path):
                    dest_path = os.path.join(temp_collections_dir, item)
                    if os.path.exists(dest_path):
                        # If it exists, remove it first to avoid errors
                        shutil.rmtree(dest_path)
                    shutil.copytree(item_path, dest_path)
                    print(f"Copied collection: {item}")
        else:
            print(f"Warning: Collections directory not found at {project_collections_dir}")
        
        return temp_collections_dir
    
    def overlay_mock_modules(self, temp_collections_dir):
        """
        Overlay mock modules on the temporary collections to override behavior
        
        Args:
            temp_collections_dir: Path to the temporary collections directory
        """
        # Get the path to the mock collections
        mock_collections_dir = os.path.join(self.parent_dir, 'mock_collections', 'ansible_collections')
        
        if os.path.exists(mock_collections_dir):
            print(f"Overlaying mock modules from {mock_collections_dir}")
            # Walk through the mock collections directory structure
            for root, dirs, files in os.walk(mock_collections_dir):
                # Calculate the relative path to maintain structure
                rel_path = os.path.relpath(root, mock_collections_dir)
                target_dir = os.path.join(temp_collections_dir, rel_path)
                
                # Create the target directory if it doesn't exist
                os.makedirs(target_dir, exist_ok=True)
                
                # Copy each file, overwriting any existing files
                for file in files:
                    source_file = os.path.join(root, file)
                    target_file = os.path.join(target_dir, file)
                    print(f"Copying mock module: {os.path.relpath(target_file, temp_collections_dir)}")
                    shutil.copy2(source_file, target_file)
        else:
            print(f"Warning: Mock collections directory not found at {mock_collections_dir}")
    
    def run_playbook_with_scenario(self, playbook_path, scenario_name, inventory_path=None, extra_vars=None, 
                                  keep_mocks=False):
        """
        Run an Ansible playbook with a specific test scenario
        
        Args:
            playbook_path: Path to the playbook to test
            scenario_name: Name of the scenario to use
            inventory_path: Path to inventory file (optional)
            extra_vars: Dictionary of extra variables to pass (optional)
            keep_mocks: Whether to keep the mock files after execution (default: False)
        
        Returns:
            tuple: (success, result_dict)
        """
        # Resolve playbook path - handle both absolute and relative paths
        if not os.path.isabs(playbook_path):
            # For relative paths, try both from current dir and from project root
            if os.path.exists(playbook_path):
                playbook_path = os.path.abspath(playbook_path)
            else:
                # Try relative to project root
                project_relative_path = os.path.join(self.project_dir, playbook_path)
                if os.path.exists(project_relative_path):
                    playbook_path = project_relative_path
                else:
                    print(f"Error: Playbook not found at {playbook_path} or {project_relative_path}")
                    return False, {"error": f"Playbook not found: {playbook_path}"}
        
        # Verify that the playbook exists
        if not os.path.exists(playbook_path):
            print(f"Error: Playbook not found at {playbook_path}")
            return False, {"error": f"Playbook not found: {playbook_path}"}
        
        print(f"Using playbook: {playbook_path}")
        
        # Handle inventory path in the same way
        if inventory_path and not os.path.isabs(inventory_path):
            if os.path.exists(inventory_path):
                inventory_path = os.path.abspath(inventory_path)
            else:
                # Try relative to project root
                project_relative_path = os.path.join(self.project_dir, inventory_path)
                if os.path.exists(project_relative_path):
                    inventory_path = project_relative_path
        
        # Load the test scenario
        try:
            scenario = ScenarioFactory.load_scenario(scenario_name)
            print(f"Using scenario: {scenario.get_name()}")
            print(f"Description: {scenario.get_description()}")
        except FileNotFoundError as e:
            print(f"Error: {str(e)}")
            return False, {"error": str(e)}
        
        # Create a temporary directory for the test environment
        self.temp_dir = os.path.join(tempfile.gettempdir(), f"ansible_test_{uuid.uuid4().hex}")
        os.makedirs(self.temp_dir, exist_ok=True)
        print(f"Created temporary directory: {self.temp_dir}")
        
        # 1. Copy real collections to the temporary directory
        self.temp_collections_dir = self.copy_real_collections_to_temp(self.temp_dir)
        
        # 2. Overlay mock modules on the temporary collections
        self.overlay_mock_modules(self.temp_collections_dir)
        
        
        try:
            # Create temp files for module configs using ModuleMockManager
            # Dynamically extract module names from scenario's service_mocks
            service_mocks = getattr(scenario, 'scenario_data', {}).get('service_mocks', {})
            module_names = list(service_mocks.keys())
            self.module_mock_manager = ModuleMockManager(self.temp_dir)
            module_configs = self.module_mock_manager.create_mock_configs(scenario, module_names)
            self.module_temp_files = self.module_mock_manager.module_temp_files

            # Set up the environment variables for the mock modules
            env = os.environ.copy()
            env = self.module_mock_manager.set_env_vars(env)
            

            # TODO: Store it a proper place
            # Ensure callback_plugins path is correctly set
            env['ANSIBLE_TEST_TMP_DIR'] = self.temp_dir
            
            # Set the ANSIBLE_COLLECTIONS_PATH to include our mock collections
            env['ANSIBLE_COLLECTIONS_PATH'] = self.temp_collections_dir
            print(f"Using temporary collections path: {self.temp_collections_dir}")
            
            # Add Python path for imports
            if 'PYTHONPATH' in env:
                env['PYTHONPATH'] = f"{self.parent_dir}:{env['PYTHONPATH']}"
            else:
                env['PYTHONPATH'] = self.parent_dir
            
            # Prepare the Ansible Runner configuration
            verbosity = 1  # Similar to '-v' flag in command line
            
            # Process and finalize extra_vars
            processed_extra_vars = extra_vars or {}
                       
            # Prepare the inventory - ansible-runner accepts either a file path or an inventory dict
            inventory = inventory_path
            
            # Create a temporary directory for Ansible Runner artifacts
            runner_artifact_dir = os.path.join(self.temp_dir, 'artifacts')
            os.makedirs(runner_artifact_dir, exist_ok=True)
            
            # Print information about the run
            print(f"Running playbook: {playbook_path}")
            if inventory:
                print(f"Using inventory: {inventory}")
            if processed_extra_vars:
                print(f"Using extra vars: {processed_extra_vars}")
            
            # Run the playbook using ansible-runner
            try:
                runner = ansible_runner.run(
                    playbook=playbook_path,
                    inventory=inventory,
                    extravars=processed_extra_vars,
                    verbosity=verbosity,
                    artifact_dir=runner_artifact_dir,
                    envvars=env,
                    quiet=False  # Set to True to reduce console output
                )
                
                # Check if the playbook execution was successful
                playbook_success = runner.rc == 0
                                   
                # Print a more detailed verification report
                print("\nVerification Results:")
                
                # Verify expected module calls using the scenario's verification mechanism
                verification_results = scenario.run_verifiers(playbook_statistics=self.playbook_statistics())
                
                # Determine the overall pass/fail status of the verification
                # Check if all verification strategies passed by looking at their get_status() results
                verification_passed = all(strategy.get_status() for strategy in scenario.verification_strategies)
                
                # Check if we're expecting the playbook to fail using the scenario's method
                expected_failure = scenario.expects_failure()
                        
                # If we expected the playbook to fail and it did, that's a success from a test perspective
                # The overall test succeeds if either:
                # 1. The playbook was supposed to succeed and did succeed (playbook_success and verification_passed)
                # 2. The playbook was supposed to fail and did fail (expected_failure and not playbook_success)
                all_passed = verification_passed
                
                print(f"\nPlaybook execution: {'SUCCESS' if playbook_success else 'FAILED'}")
                print(f"Expected failure: {'YES' if expected_failure else 'NO'}")
                print(f"Verification result: {'PASS' if verification_passed else 'FAIL'}")
                
                # Determine overall success: If we're expecting failure and got failure, or expecting success and got success
                test_success = (expected_failure and not playbook_success) or (not expected_failure and playbook_success)
                overall_success = test_success and verification_passed
                
                print(f"Overall test result: {'PASS' if overall_success else 'FAIL'}")
                
                # Update the instance properties for easy access
                self.success = overall_success
                self.execution_details = {
                    'success': overall_success,
                    'playbook_success': playbook_success,
                    'expected_failure': expected_failure,
                    'verification_passed': verification_passed,
                    'returncode': runner.rc,
                    'verification': verification_results,
                    'mock_dir': self.temp_dir if keep_mocks else None,
                    'artifacts_dir': runner_artifact_dir,
                }
                
                # Return results - we're returning overall_success as the first return value
                # which determines the process exit code
                return overall_success, self.execution_details
                
            except Exception as e:
                print(f"Error running playbook with ansible-runner: {str(e)}")
                return False, {"error": str(e)}
            
        finally:          
            # Clean up the temporary files only if not keeping mocks
            if not keep_mocks:
                self.cleanup(verbose=True)
            else:
                print(f"\n*** KEEPING MOCK FILES FOR DEBUGGING ***")
                print(f"Mock directory: {self.temp_dir}")
                print(f"Temporary collections directory: {self.temp_collections_dir}")
                print(f"Mock files:")
                for file_path in self.module_temp_files:
                    if os.path.exists(file_path):
                        print(f"  - {file_path}")

    def cleanup(self, verbose: bool = True) -> bool:
        """
        Clean up all artifacts generated during the test run
        
        Args:
            verbose: If True, print information about the cleanup process
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        success = True
        
        try:
            # Clean up the mock module manager resources
            if self.module_mock_manager:
                if verbose:
                    print("Cleaning up module mock resources...")
                self.module_mock_manager.cleanup()
                
            # Remove the temporary directory and all its contents if it exists
            if self.temp_dir and os.path.exists(self.temp_dir):
                if verbose:
                    print(f"Removing temporary directory: {self.temp_dir}")
                try:
                    shutil.rmtree(self.temp_dir)
                    if verbose:
                        print("Temporary directory removed successfully.")
                except Exception as e:
                    if verbose:
                        print(f"Error removing temporary directory: {str(e)}")
                    success = False
                    
            # Reset instance variables
            self.temp_dir = None
            self.temp_collections_dir = None
            self.module_temp_files = []
            self.module_mock_manager = None
            
            return success
            
        except Exception as e:
            if verbose:
                print(f"Error during cleanup process: {str(e)}")
            return False

    def playbook_statistics(self):
        """Get the playbook statistics from the summary data file"""
        """Read playbook statistics from the playbook_statistics.json file"""
        summary_data = {}
        summary_file = 'playbook_statistics.json'
        if self.temp_dir:
            summary_file = os.path.join(self.temp_dir, 'playbook_statistics.json')
        
        try:
            # Check if the summary file exists
            if os.path.exists(summary_file):
                with open(summary_file, 'r') as f:
                    summary_data = json.load(f)
                return summary_data
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error reading module call statistics: {str(e)}")
            
        return {}


    @staticmethod
    def parse_arguments():
        """Parse command line arguments for the test runner"""
        parser = argparse.ArgumentParser(description='Run Ansible playbooks with scenario-based testing')
        parser.add_argument('playbook', help='Path to the playbook to test')
        parser.add_argument('--scenario', '-s', required=True, help='Name of the scenario to use')
        parser.add_argument('--inventory', '-i', help='Path to inventory file')
        parser.add_argument('--extra-var', '-e', action='append', help='Extra variables (key=value format)')
        parser.add_argument('--keep-mocks', '-k', action='store_true', help='Keep mock files after execution for debugging')
        
        return parser.parse_args()


def main():
    """Main function for the test runner"""
    args = PlaybookRunner.parse_arguments()
    
    # Process extra vars
    extra_vars = {}
    if args.extra_var:
        for var in args.extra_var:
            if '=' in var:
                key, value = var.split('=', 1)
                extra_vars[key] = value
    
    # Create runner instance
    runner = PlaybookRunner()
    
    try:
        # Run the playbook with the specified scenario
        success, result = runner.run_playbook_with_scenario(
            args.playbook,
            args.scenario,
            inventory_path=args.inventory,
            extra_vars=extra_vars,
            keep_mocks=args.keep_mocks
        )
        
        # Exit with appropriate return code
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest execution interrupted by user.")
        if not args.keep_mocks:
            print("Cleaning up resources...")
            runner.cleanup(verbose=True)
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"Error in test execution: {str(e)}")
        if not args.keep_mocks:
            print("Cleaning up resources...")
            runner.cleanup(verbose=True)
        sys.exit(1)


if __name__ == '__main__':
    main()