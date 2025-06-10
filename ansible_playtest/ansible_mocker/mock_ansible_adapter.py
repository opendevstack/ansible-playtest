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
            with open(file_path, "r") as f:
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

        module.warn(f"MockAnsibleAdapter.run_mock_module called for {module_name}")
        module.warn(f"Current file path: {__file__}")
        module.warn(
            f"Mocking is enabled for {module_name}, looking for mock config {mock_config_path}"
        )

        if not mock_config_path:
            module.debug(f"No mock config path found for {module_name}")
            module.fail_json(changed=False, msg="No mock config found")

        mock_config = MockAnsibleAdapter.load_mock_config(mock_config_path)

        if not mock_config:
            module.debug(f"Mock config not found at {mock_config_path}")
            module.fail_json(changed=False, msg="No mock config found")

        response_data = dict(mock_config)

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
            module.fail_json(changed=False, msg=response_data["error_message"])

        module.warn(f"Exiting with mock config: {response_data}")
        module.exit_json(**response_data)
