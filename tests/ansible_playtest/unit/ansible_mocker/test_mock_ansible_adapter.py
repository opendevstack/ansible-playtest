"""
Tests for MockAnsibleAdapter class in mock_ansible_adapter.py
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ansible_playtest.ansible_mocker.mock_ansible_adapter import MockAnsibleAdapter


class TestMockAnsibleAdapter:
    """Test cases for MockAnsibleAdapter class"""

    def create_mock_ansible_module(self, params=None):
        """Helper method to create a mock AnsibleModule with specific parameters"""
        mock_module = Mock()
        mock_module.params = params or {}
        mock_module.warn = Mock()
        mock_module.log = Mock()
        return mock_module

    def test_get_response_data_backwards_compatibility_dict(self):
        """Test get_response_data with non-list config (backwards compatibility)"""
        # Arrange
        mock_config = {"changed": True, "msg": "Success"}
        mock_module = self.create_mock_ansible_module()
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Success"}
        assert isinstance(result, dict)

    def test_get_response_data_list_default_first_entry(self):
        """Test get_response_data returns first entry when no task_parameters match"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {"changed": False, "msg": "Other response"}
        ]
        mock_module = self.create_mock_ansible_module()
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Default response"}
        mock_module.warn.assert_called_with(
            "No matching mock response found, using default: {'changed': True, 'msg': 'Default response'}"
        )

    def test_get_response_data_matching_task_parameters(self):
        """Test get_response_data with matching task_parameters"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {
                "task_parameters": {"name": "test_service", "state": "started"},
                "changed": True,
                "msg": "Service started"
            },
            {
                "task_parameters": {"name": "other_service", "state": "stopped"},
                "changed": False,
                "msg": "Service stopped"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service",
            "state": "started",
            "enabled": True
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Service started"}
        mock_module.warn.assert_any_call("Parameters match: True")
        mock_module.warn.assert_any_call("Found matching mock response: {'changed': True, 'msg': 'Service started'}")

    def test_get_response_data_partial_parameter_match(self):
        """Test get_response_data when only some parameters match"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {
                "task_parameters": {"name": "test_service", "state": "stopped"},
                "changed": False,
                "msg": "Service stopped"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service",
            "state": "started"  # Different state
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Default response"}
        mock_module.warn.assert_called_with(
            "No matching mock response found, using default: {'changed': True, 'msg': 'Default response'}"
        )

    def test_get_response_data_missing_parameter_in_module(self):
        """Test get_response_data when required parameter is missing from module"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {
                "task_parameters": {"name": "test_service", "state": "started"},
                "changed": True,
                "msg": "Service started"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service"
            # Missing 'state' parameter
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Default response"}
        mock_module.warn.assert_any_call("Parameter 'state' not found in module params")
        mock_module.warn.assert_called_with(
            "No matching mock response found, using default: {'changed': True, 'msg': 'Default response'}"
        )

    def test_get_response_data_string_comparison_template_variables(self):
        """Test get_response_data handles string comparison for template variables"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {
                "task_parameters": {"port": "8080", "enabled": True},
                "changed": True,
                "msg": "Port configured"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "port": 8080,  # Integer value
            "enabled": True  # Boolean value
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Port configured"}

    def test_get_response_data_multiple_matching_entries_returns_first_match(self):
        """Test get_response_data returns first matching entry when multiple match"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {
                "task_parameters": {"name": "test_service"},
                "changed": True,
                "msg": "First match"
            },
            {
                "task_parameters": {"name": "test_service"},
                "changed": False,
                "msg": "Second match"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service"
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "First match"}

    def test_get_response_data_no_task_parameters_uses_default(self):
        """Test get_response_data with entries without task_parameters uses default"""
        # Arrange
        mock_config = [
            {"changed": True, "msg": "Default response"},
            {"changed": False, "msg": "No task params response"}
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service"
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert result == {"changed": True, "msg": "Default response"}
        mock_module.warn.assert_called_with(
            "No matching mock response found, using default: {'changed': True, 'msg': 'Default response'}"
        )

    def test_get_response_data_task_parameters_popped_from_response(self):
        """Test get_response_data removes task_parameters from final response"""
        # Arrange
        mock_config = [
            {
                "task_parameters": {"name": "test_service"},
                "changed": True,
                "msg": "Service configured",
                "service_name": "test_service"
            }
        ]
        mock_module = self.create_mock_ansible_module({
            "name": "test_service"
        })
        
        # Act
        result = MockAnsibleAdapter.get_response_data(mock_config, mock_module)
        
        # Assert
        assert "task_parameters" not in result
        assert result == {
            "changed": True,
            "msg": "Service configured",
            "service_name": "test_service"
        }

    def test_get_response_data_empty_list_raises_index_error(self):
        """Test get_response_data with empty list raises IndexError"""
        # Arrange
        mock_config = []
        mock_module = self.create_mock_ansible_module()
        
        # Act & Assert
        with pytest.raises(IndexError):
            MockAnsibleAdapter.get_response_data(mock_config, mock_module)