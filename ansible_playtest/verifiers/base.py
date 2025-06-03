"""
Base verification strategy for Ansible test framework
"""
from abc import ABC, abstractmethod

class VerificationStrategy(ABC):
    """Abstract base class for verification strategies"""
    
    # Constants for output formatting
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    PASS_SYMBOL = "\u2713"  # Checkmark
    FAIL_SYMBOL = "\u2717"  # X mark
    
    @abstractmethod
    def verify(self, scenario_data, playbook_stats):
        """
        Verify the scenario according to the strategy
        
        Args:
            scenario_data: The full scenario data from the YAML file
            playbook_stats: The playbook_stats call statistics to verify against
            
        Returns:
            dict: Verification results that must include an '_overall_pass' key 
                 with a boolean value indicating overall verification status
        """
        pass
    
    def format_result_line(self, passed, text):
        """
        Format a single result line with appropriate color and symbol
        
        Args:
            passed: Boolean indicating if the check passed
            text: The text to display after the symbol
            
        Returns:
            str: Formatted result line
        """
        color = self.GREEN if passed else self.RED
        symbol = self.PASS_SYMBOL if passed else self.FAIL_SYMBOL
        return f"{color}{symbol}{self.RESET} {text}"
    
    def print_results(self, verification_results, verifier_name):
        """
        Print verification results in a standardized format
        
        Args:
            verification_results: The results from the verify method
            verifier_name: The name of the verifier for displaying purposes
        """
        if not verification_results:
            return
            
        print(f"\n{verifier_name} verification results:")
        
        # Get the overall status
        overall_pass = self.get_overall_status(verification_results)
        
        # Print overall status
        result_text = f"Overall {verifier_name.lower()} verification: {'PASSED' if overall_pass else 'FAILED'}"
        print(self.format_result_line(overall_pass, result_text))
        
        # Print individual results if applicable
        for key, value in verification_results.items():
            if key == '_overall_pass':
                continue
                
            if isinstance(value, dict) and 'passed' in value:
                result_text = f"{key}: {'passed' if value['passed'] else 'failed'}"
                print(self.format_result_line(value['passed'], result_text))
        
    def get_overall_status(self, verification_results):
        """
        Get the overall status from verification results
        
        Args:
            verification_results: The verification results to check
            
        Returns:
            bool: True if all verifications passed, False otherwise
        """
        # Return the _overall_pass value if it exists
        if '_overall_pass' in verification_results:
            return verification_results['_overall_pass']
            
        # Otherwise iterate through all results to determine overall status
        for key, value in verification_results.items():
            if key != '_overall_pass':  # Skip the overall status key itself
                if isinstance(value, dict) and 'passed' in value and not value['passed']:
                    return False
        
        return True