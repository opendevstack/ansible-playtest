"""
Parameter validation verification for Ansible test framework
"""
from .base import VerificationStrategy

class ParameterValidationVerifier(VerificationStrategy):
    """Verification strategy for validating module call parameters"""
    
    def __init__(self):
        """Initialize the verifier"""
        self.overall_status = True  # Default to success
        
    def verify(self, scenario_data, playbook_stats):
        """
        Verify that module parameters match expected values
        
        Args:
            scenario_data: The full scenario data from the YAML file
            playbook_stats: The playbook call statistics to verify against
            
        Returns:
            dict: Verification results keyed by module name
        """
        verification_results = {}
        
        # Check if parameter validation is defined in the scenario
        if 'verify' not in scenario_data or 'parameter_validation' not in scenario_data['verify']:
            self.overall_status = True
            return {'_overall_pass': True}
        
        param_validations = scenario_data['verify']['parameter_validation']
        
        # Get the detailed module call data if available
        module_call_details = playbook_stats.get('call_details', {})
        
        for module_name, expected_params in param_validations.items():
            # Skip if this module has no expected parameters defined
            if not expected_params:
                continue
                
            module_result = {
                'passed': True,
                'parameter_validation': True,
                'details': []
            }
            
            # Get actual calls for this module
            actual_calls = module_call_details.get(module_name, [])
            
            # For each expected call/parameter set
            for call_idx, expected_call_params in enumerate(expected_params):
                # If we have more expected calls than actual calls, mark as failed
                if call_idx >= len(actual_calls):
                    module_result['passed'] = False
                    module_result['details'].append({
                        'call_index': call_idx,
                        'status': 'missing',
                        'expected': expected_call_params
                    })
                    continue
                
                # Get the actual parameters for this call
                actual_params = actual_calls[call_idx].get('params', {})
                
                # Compare parameters
                param_failures = []
                for param_name, expected_value in expected_call_params.items():
                    if param_name not in actual_params:
                        param_failures.append({
                            'param': param_name, 
                            'expected': expected_value, 
                            'actual': 'missing'
                        })
                    elif str(actual_params[param_name]).strip() != str(expected_value).strip():
                        param_failures.append({
                            'param': param_name, 
                            'expected': expected_value, 
                            'actual': actual_params[param_name]
                        })
                
                # Record this call's verification status
                call_status = 'passed' if not param_failures else 'failed'
                module_result['details'].append({
                    'call_index': call_idx,
                    'status': call_status,
                    'failures': param_failures
                })
                
                # Update overall status
                if call_status == 'failed':
                    module_result['passed'] = False
            
            verification_results[module_name] = module_result
      
        # Add overall pass status
        verification_results['_overall_pass'] = all(
            result.get('passed', True) for result in verification_results.values()
        ) if verification_results else True
        
        # Update the overall status of the verifier
        self.overall_status = verification_results['_overall_pass']
        
        # Print the verification results
        self._print_parameter_results(verification_results)
        
        return verification_results
        
    def _print_parameter_results(self, verification_results):
        """
        Print parameter validation verification results
        
        Args:
            verification_results: The verification results to print
        """
        if not verification_results:
            return
            
        print(f"\nParameter validation verification results:")
        
        for module_name, result in verification_results.items():
            if module_name == '_overall_pass':
                continue
                
            passed = result.get('passed', True)
            result_text = f"{module_name}: {'passed' if passed else 'failed'}"
            print(self.format_result_line(passed, result_text))
            
            # Print failure details
            if not passed and 'details' in result:
                for detail in result['details']:
                    if detail.get('status') == 'missing':
                        print(f"  {self.RED}Call {detail.get('call_index')} missing{self.RESET}")
                    elif detail.get('status') == 'failed' and 'failures' in detail:
                        print(f"  {self.RED}Call {detail.get('call_index')} parameter errors:{self.RESET}")
                        for failure in detail['failures'][:3]:  # Limit to first 3 failures to keep output concise
                            print(f"    Parameter '{failure['param']}': expected={failure['expected']}, got={failure['actual']}")
                        if len(detail['failures']) > 3:
                            print(f"    ... and {len(detail['failures']) - 3} more parameter errors")
                            
    def get_status(self):
        """
        Get the overall pass/fail status of this verifier
        
        Returns:
            bool: True if all verifications passed, False otherwise
        """
        return self.overall_status