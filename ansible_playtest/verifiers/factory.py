"""
Factory for creating verification strategies based on scenario configuration
"""

from .module_call import ModuleCallCountVerifier
from .parameter import ParameterValidationVerifier
from .sequence import CallSequenceVerifier
from .error import ErrorVerifier


class VerificationStrategyFactory:
    """Factory for creating verification strategies based on scenario config"""

    @staticmethod
    def create_strategies(scenario_data):
        """
        Create appropriate verification strategies based on scenario configuration

        Args:
            scenario_data: The full scenario data from the YAML file

        Returns:
            list: List of verification strategy instances
        """
        strategies = []

        # Check for verification strategies in the scenario data
        if "verify" in scenario_data:
            verify_config = scenario_data["verify"]

            # Add module call count verification if configured
            if "expected_calls" in verify_config:
                strategies.append(ModuleCallCountVerifier())

            # Add parameter validation strategy if configured
            if "parameter_validation" in verify_config:
                strategies.append(ParameterValidationVerifier())

            # Add call sequence verification if configured
            if "call_sequence" in verify_config:
                strategies.append(CallSequenceVerifier())

            # Add error verification if configured
            if "expected_errors" in verify_config:
                strategies.append(ErrorVerifier())

        return strategies
