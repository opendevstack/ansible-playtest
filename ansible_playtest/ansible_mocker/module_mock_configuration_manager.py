"""
ModuleMockConfigurationManager class for managing mock configurations and environment variables for Ansible module mocking.

This module provides functionality to create, manage, and clean up mock configurations
for Ansible modules during testing. It allows specifying mock responses for modules
and setting environment variables to enable the mocks during Ansible playbook execution.
"""

import os
import json


class ModuleMockConfigurationManager:
    """Handles creation of mock config files and environment variables for Ansible module mocking."""

    def __init__(self, temp_dir):
        self.temp_dir = temp_dir
        self.module_temp_files = []
        self.module_configs = {}

    def create_mock_configs(self, scenario, module_names):
        """
        Create mock config files for the given modules using scenario data.
        Args:
            scenario: The scenario object providing mock responses.
            module_names: List of module names to mock.
        Returns:
            dict: Mapping of module name to config file path.
        """
        for module_name in module_names:
            mock_data = scenario.get_mock_response(module_name)
            file_path = os.path.join(self.temp_dir, f"{module_name}_mock_config.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(mock_data, f)
            self.module_temp_files.append(file_path)
            self.module_configs[module_name] = file_path
        return self.module_configs

    def set_env_vars(self, env):
        """
        Set environment variables for the mocked modules.
        Args:
            env: The environment dict to update.
        Returns:
            dict: The updated environment dict.
        """
        for module_name, config_path in self.module_configs.items():
            env_module_name = module_name.replace(".", "_").upper()
            env[f"ANSIBLE_MOCK_{env_module_name}_CONFIG"] = config_path
            env[f"ANSIBLE_MOCK_{env_module_name}_ENABLED"] = "true"
        return env

    def cleanup(self):
        """
        Remove all created mock config files.
        """
        for file_path in self.module_temp_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except (IOError, OSError):
                pass
