"""
Module call count verification for Ansible test framework
"""
from .base import VerificationStrategy

class ModuleCallCountVerifier(VerificationStrategy):
    """Verification strategy for module call counts"""
    
    def __init__(self):
        """Initialize the verifier"""
        self.overall_status = True  # Default to success
        
    def verify(self, scenario_data, playbook_stats):
        """
        Verify that modules were called the expected number of times
        
        Args:
            scenario_data: The full scenario data from the YAML file
            playbook_stats: The module call statistics to verify against
            
        Returns:
            dict: Verification results keyed by module name
        """
        # Look for expected_calls under the verify key, then fall back to top level for backward compatibility
        expected_calls = {}
        if 'verify' in scenario_data and 'expected_calls' in scenario_data['verify']:
            expected_calls = scenario_data['verify']['expected_calls']
            
        verification_results = {}
        module_calls = playbook_stats.get('module_calls', {})
        for module_name, expected_count in expected_calls.items():
            actual_count = module_calls.get(module_name, 0)
            verification_results[module_name] = {
                'expected': expected_count,
                'actual': actual_count,
                'passed': expected_count == actual_count
            }
        
        # Add overall pass status to help with debugging
        verification_results['_overall_pass'] = all(
            result['passed'] for result in verification_results.values()
        ) if verification_results else True
        
        # Set the overall status of the verifier
        self.overall_status = verification_results['_overall_pass']
        
        # Print the verification results
        self._print_call_count_results(verification_results)

        return verification_results
        
    def _print_call_count_results(self, verification_results):
        """
        Print module call count verification results
        
        Args:
            verification_results: The verification results to print
        """
        if not verification_results:
            return
            
        print(f"\nModule call verification results:")
        
        for module_name, result in verification_results.items():
            if module_name == '_overall_pass':
                continue
                
            result_text = f"{module_name}: expected={result['expected']}, actual={result['actual']}"
            print(self.format_result_line(result['passed'], result_text))
            
            # Add failure details if applicable
            if not result['passed']:
                diff = result['actual'] - result['expected']
                if diff > 0:
                    print(f"  {self.RED}Error: Module called {diff} more times than expected{self.RESET}")
                else:
                    print(f"  {self.RED}Error: Module called {abs(diff)} fewer times than expected{self.RESET}")

    def get_status(self):
        """
        Get the overall pass/fail status of this verifier
        
        Returns:
            bool: True if all verifications passed, False otherwise
        """
        return self.overall_status