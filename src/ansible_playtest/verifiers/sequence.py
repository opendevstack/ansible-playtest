"""
Call sequence verification for Ansible test framework
"""
from .base import VerificationStrategy

class CallSequenceVerifier(VerificationStrategy):
    """Verification strategy to check module call sequence/order"""
    
    def __init__(self):
        """Initialize the verifier"""
        self.overall_status = True  # Default to success
    
    def verify(self, scenario_data, playbook_stats):
        """
        Verify that modules were called in the expected sequence
        
        Args:
            scenario_data: The full scenario data from the YAML file
            playbook_stats: The playbook call statistics to verify against
            
        Returns:
            dict: Verification results keyed by verification step
        """
        verification_results = {}
        
        # Check if call sequence validation is defined in the scenario
        if 'verify' not in scenario_data or 'call_sequence' not in scenario_data['verify']:
            # If no call sequence is defined, consider it a pass
            self.overall_status = True
            return {'_overall_pass': True}
        
        expected_sequence = scenario_data['verify']['call_sequence']
        actual_sequence = playbook_stats.get('call_sequence', [])
        
        # Initialize the verification results
        verification_results['expected_sequence'] = expected_sequence
        verification_results['actual_sequence'] = actual_sequence
        
        # Perform non-strict sequence validation
        # This allows other modules to be called between expected modules
        errors = []
        expected_idx = 0
        last_found_idx = -1
        
        # Iterate through expected sequence
        for expected_idx, expected_module in enumerate(expected_sequence):
            # Try to find this module call in the remaining actual sequence
            found = False
            
            # Search for the expected module in the remaining actual sequence
            for actual_idx in range(last_found_idx + 1, len(actual_sequence)):
                if actual_sequence[actual_idx] == expected_module:
                    last_found_idx = actual_idx
                    found = True
                    break
            
            # If we didn't find this expected module in the sequence
            if not found:
                errors.append(f"Missing expected module: {expected_module} - should appear after position {last_found_idx}")
        
        verification_results['errors'] = errors
        verification_results['_overall_pass'] = len(errors) == 0
        
        # Set the overall status
        self.overall_status = verification_results['_overall_pass']
        
        # Print the verification results
        self._print_sequence_results(verification_results)
        
        return verification_results
    
    def _print_sequence_results(self, verification_results):
        """
        Print sequence verification results
        
        Args:
            verification_results: The verification results to print
        """
        if not verification_results:
            return
            
        print(f"\nCall sequence verification results:")
        
        passed = verification_results.get('_overall_pass', False)
        result_text = f"call sequence verification: {'passed' if passed else 'failed'}"
        print(self.format_result_line(passed, result_text))
        
        # Print failure details
        if not passed and 'errors' in verification_results:
            for error in verification_results['errors']:
                print(f"  {self.RED}{error}{self.RESET}")
            
            # Show the expected vs actual sequences
            print(f"\n  {self.BLUE}Expected sequence:{self.RESET}")
            for idx, module in enumerate(verification_results.get('expected_sequence', [])):
                print(f"    {idx}: {module}")
                
            print(f"\n  {self.BLUE}Actual sequence:{self.RESET}")
            for idx, module in enumerate(verification_results.get('actual_sequence', [])):
                print(f"    {idx}: {module}")
    
    def get_status(self):
        """
        Get the overall pass/fail status of this verifier
        
        Returns:
            bool: True if all verifications passed, False otherwise
        """
        return self.overall_status