"""
Error verification for Ansible test framework
"""
from .base import VerificationStrategy

class ErrorVerifier(VerificationStrategy):
    """Verification strategy for expected errors in playbook execution"""
    
    def __init__(self):
        """Initialize the verifier"""
        self.overall_status = True  # Default to success
        
    def verify(self, scenario_data, playbook_stats):
        """
        Verify that expected errors were encountered during playbook execution
        
        Args:
            scenario_data: The full scenario data from the YAML file
            playbook_stats: The playbook_stats call statistics to verify against
            
        Returns:
            dict: Verification results for error matching
        """
        # Default empty result with pass status
        verification_results = {'error_checks': [], '_overall_pass': True}
        
        # Check if expected_errors is defined in the scenario
        if 'verify' in scenario_data and 'expected_errors' in scenario_data['verify']:
            expected_errors = scenario_data['verify']['expected_errors']
            actual_errors = playbook_stats.get('errors', [])
            
            # No expected errors defined, nothing to verify
            if not expected_errors:
                return verification_results
                
            # Process each expected error
            all_errors_found = True
            for expected_error in expected_errors:
                error_found = False
                expected_message = expected_error.get('message', '')
                expected_task = expected_error.get('task', '')
                
                # Check each actual error for a match
                for actual_error in actual_errors:
                    actual_message = actual_error.get('message', '')
                    actual_task = actual_error.get('task', '')
                    
                    # Check if both message and task match, or just message if task not specified
                    if expected_message in actual_message:
                        if not expected_task or expected_task in actual_task:
                            error_found = True
                            break
                
                # Record the result for this expected error
                error_result = {
                    'expected_message': expected_message,
                    'expected_task': expected_task,
                    'found': error_found,
                    'actual_errors': [
                        {'task': e.get('task', ''), 'message': e.get('message', '')}
                        for e in actual_errors
                    ] if not error_found else []  # Only include actual errors if expected error was not found
                }
                verification_results['error_checks'].append(error_result)
                
                # Update overall status
                if not error_found:
                    all_errors_found = False
            
            # Check for process failure (if playbook failed but should have succeeded)
            process_failure_expected = any(
                expected_error.get('expect_process_failure', False)
                for expected_error in expected_errors
            )
            
            # Check process failure by examining the host recap data
            host_failed_count = 0
            if 'play_recap' in playbook_stats and 'hosts' in playbook_stats['play_recap']:
                # Sum up the failures across all hosts
                for host_stats in playbook_stats['play_recap']['hosts'].values():
                    host_failed_count += host_stats.get('failures', 0)
            
            # Fallback to total_failures if play_recap is not available
            process_failed = host_failed_count > 0 if host_failed_count is not None else playbook_stats.get('total_failures', 0) > 0
            
            # Record process failure verification
            verification_results['process_failure'] = {
                'expected': process_failure_expected,
                'actual': process_failed,
                'passed': process_failure_expected == process_failed
            }
            
            # Update overall pass status based on error checks and process failure check
            verification_results['_overall_pass'] = all_errors_found and verification_results['process_failure']['passed']
            self.overall_status = verification_results['_overall_pass']
            
            # Print verification results
            self._print_error_verification_results(verification_results)
            
        return verification_results
        
    def _print_error_verification_results(self, results):
        """
        Print the error verification results in a readable format
        
        Args:
            results: The verification results dictionary
        """
        print(f"\nError Verification Results")
        
        overall_status = results.get('_overall_pass', False)
        overall_symbol = self.PASS_SYMBOL if overall_status else self.FAIL_SYMBOL
        overall_color = self.GREEN if overall_status else self.RED
        
        print(f"{overall_color}{overall_symbol}{self.RESET} Overall Error Verification: "
              f"{overall_color}{'PASSED' if overall_status else 'FAILED'}{self.RESET}")
        
        # Print process failure verification if available
        if 'process_failure' in results:
            process_result = results['process_failure']
            process_status = process_result.get('passed', False)
            process_symbol = self.PASS_SYMBOL if process_status else self.FAIL_SYMBOL
            process_color = self.GREEN if process_status else self.RED
            
            print(f"  {process_color}{process_symbol} Process Failure: "
                  f"Expected: {process_result['expected']}, "
                  f"Actual: {process_result['actual']}{self.RESET}")
        
        # Print individual error check results
        for check in results.get('error_checks', []):
            check_status = check.get('found', False)
            check_symbol = self.PASS_SYMBOL if check_status else self.FAIL_SYMBOL
            check_color = self.GREEN if check_status else self.RED
            
            # Format the error check display
            task_info = f" in task '{check['expected_task']}'" if check.get('expected_task') else ""
            print(f"  {check_color}{check_symbol} Expected error{task_info}: "
                  f"{check['expected_message']}{self.RESET}")
            
            # If the check failed, print the actual errors
            if not check_status and check.get('actual_errors'):
                print(f"    {self.YELLOW}Actual errors found:{self.RESET}")
                for actual_error in check['actual_errors']:
                    actual_task = actual_error.get('task', '')
                    actual_message = actual_error.get('message', '')
                    print(f"    {self.YELLOW}- Task: {actual_task}, Message: {actual_message}{self.RESET}")
        
    def get_status(self):
        """
        Get the overall pass/fail status of this verifier
        
        Returns:
            bool: True if all verifications passed, False otherwise
        """
        return self.overall_status
