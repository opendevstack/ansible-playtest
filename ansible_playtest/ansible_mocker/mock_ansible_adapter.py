"""
Mock adapter for Ansible modules
"""

import os
import json
import sys
from ansible.module_utils.basic import AnsibleModule


class MockAnsibleAdapter:
    """Adapter class to handle mocking of Ansible modules"""

    @staticmethod
    def get_mock_config_path(module_name):
        """Get path to mock configuration for a module"""
        env_module_name = module_name.replace(".", "_").upper()
        env_var_name = f"ANSIBLE_MOCK_{env_module_name}_CONFIG"
        if env_var_name in os.environ:
            config_path = os.environ[env_var_name]
            return config_path
        return None

    @staticmethod
    def load_mock_config(file_path):
        """Load mock configuration from a file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config
        except (IOError, json.JSONDecodeError) as e:
            # If we can't load the mock config, log the error and return None
            error_msg = f"Error loading mock config: {str(e)}"
            sys.stderr.write(f"{error_msg}\n")
            return None

    @staticmethod
    def run_mock_module(module_name, argument_spec, supports_check_mode=False):
        module = AnsibleModule(
            argument_spec=argument_spec, supports_check_mode=supports_check_mode
        )

        mock_config_path = MockAnsibleAdapter.get_mock_config_path(module_name)

        module.warn(
            f"MockAnsibleAdapter.run_mock_module called for {module_name} (file: {__file__}). Mocking is enabled, looking for mock config at {mock_config_path}"
        )

        if not mock_config_path:
            module.fail_json(
                changed=False,
                msg=f"No mock config found, no mock config path found for {module_name}",
            )

        mock_config = MockAnsibleAdapter.load_mock_config(mock_config_path)

        if not mock_config:
            module.fail_json(
                changed=False, msg=f"No mock config found at {mock_config_path}"
            )

        # Process the mock configuration to find the appropriate response
        response_data = MockAnsibleAdapter.get_response_data(mock_config, module)

        # Check if this is a failure scenario
        is_failure = False
        if "success" in response_data:
            is_failure = not response_data["success"]
            # Remove the success entry as it's used for flow control
            del response_data["success"]

        if is_failure:
            # Handle service failure scenario
            error_msg = response_data.get("error_message", "Mock service failure")
            module.warn(f"Simulating failure for {module_name}: {error_msg}")
            module.fail_json(msg=error_msg, **response_data)

        module.warn(f"Exiting with mock config: {response_data}")
        module.exit_json(**response_data)

    @staticmethod
    def get_response_data(mock_config, module: AnsibleModule):
        """
        Process the mock configuration to find the appropriate response based on matching criteria:
        - If mock_config is not a list, return it as is (backwards compatibility)
        - If it's a list, look for entries that match task_parameters if provided
        """
        # For backwards compatibility, if not a list, return as is
        if not isinstance(mock_config, list):
            return dict(mock_config)

        # Default to the first entry if no match is found
        default_response = dict(mock_config[0])

        for mock_entry in mock_config:
            mock_entry_copy = dict(mock_entry)

            # Check parameters if provided
            if "task_parameters" in mock_entry_copy:
                task_parameters = mock_entry_copy.pop("task_parameters")
                # Assume parameters match initially
                task_params_match = True
                
                # Check if all required parameters match
                for key, value in task_parameters.items():
                    if key not in module.params:
                        task_params_match = False
                        module.warn(f"Parameter '{key}' not found in module params")
                        break
                    # Perform string comparison to handle template variables
                    if str(module.params[key]) != str(value):
                        task_params_match = False
                        break

                module.warn(f"Parameters match: {task_params_match}")

                # If parameters match, use this response
                if task_params_match:
                    module.warn(f"Found matching mock response: {mock_entry_copy}")
                    return mock_entry_copy

        # Return the default (first) response if no match found
        module.warn(
            f"No matching mock response found, using default: {default_response}"
        )
        return default_response