"""
Unit tests for virtual environment module mocking functionality
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch
from ansible_playtest.pytest_plugin.plugin_module_mocker import (
    VirtualenvAwareModuleMocker,
    VirtualenvModuleMocker
)


class TestVirtualenvAwareModuleMocker:
    """Test the VirtualenvAwareModuleMocker class"""
    
    def test_init_with_modules(self):
        """Test initialization with modules to mock"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        mocker = VirtualenvAwareModuleMocker(modules_to_mock)
        
        assert mocker.modules_to_mock == modules_to_mock
        assert mocker.mocker is None
        assert mocker.is_active is False
    
    def test_init_with_empty_modules(self):
        """Test initialization with no modules to mock"""
        mocker = VirtualenvAwareModuleMocker({})
        
        assert mocker.modules_to_mock == {}
        assert mocker.mocker is None
        assert mocker.is_active is False
    
    @patch('ansible_playtest.pytest_plugin.plugin_module_mocker.VirtualenvModuleMocker')
    def test_setup_mocks_with_virtualenv(self, mock_virtualenv_mocker):
        """Test setup_mocks with virtual environment path"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        mocker = VirtualenvAwareModuleMocker(modules_to_mock)
        
        mock_instance = Mock()
        mock_virtualenv_mocker.return_value = mock_instance
        
        mocker.setup_mocks("/path/to/venv")
        
        mock_virtualenv_mocker.assert_called_once_with(modules_to_mock, "/path/to/venv")
        mock_instance.setup_mocks.assert_called_once()
        assert mocker.is_active is True
    
    @patch('ansible_playtest.pytest_plugin.plugin_module_mocker.ModuleMocker')
    def test_setup_mocks_without_virtualenv(self, mock_module_mocker):
        """Test setup_mocks without virtual environment path"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        mocker = VirtualenvAwareModuleMocker(modules_to_mock)
        
        mock_instance = Mock()
        mock_module_mocker.return_value = mock_instance
        
        mocker.setup_mocks()
        
        mock_module_mocker.assert_called_once_with(modules_to_mock)
        mock_instance.setup_mocks.assert_called_once()
        assert mocker.is_active is True
    
    def test_setup_mocks_with_empty_modules(self):
        """Test setup_mocks with no modules to mock"""
        mocker = VirtualenvAwareModuleMocker({})
        
        # Should not raise any errors
        mocker.setup_mocks("/path/to/venv")
        
        assert mocker.mocker is None
        assert mocker.is_active is False
    
    def test_restore_mocks_active(self):
        """Test restore_mocks when mocks are active"""
        mocker = VirtualenvAwareModuleMocker({"test.module": "/path/to/mock"})
        mock_mocker = Mock()
        mocker.mocker = mock_mocker
        mocker.is_active = True
        
        mocker.restore_mocks()
        
        mock_mocker.restore_modules.assert_called_once()
        assert mocker.is_active is False
    
    def test_restore_mocks_inactive(self):
        """Test restore_mocks when mocks are not active"""
        mocker = VirtualenvAwareModuleMocker({"test.module": "/path/to/mock"})
        
        # Should not raise any errors
        mocker.restore_mocks()
        
        assert mocker.is_active is False
    
    def test_context_manager(self):
        """Test context manager functionality"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        
        with VirtualenvAwareModuleMocker(modules_to_mock) as mocker:
            assert isinstance(mocker, VirtualenvAwareModuleMocker)
            assert mocker.modules_to_mock == modules_to_mock
        
        # Context manager should call restore_mocks on exit
        # (tested indirectly through no exceptions)


class TestVirtualenvModuleMocker:
    """Test the VirtualenvModuleMocker class"""
    
    def test_init(self):
        """Test initialization"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        virtualenv_path = "/path/to/venv"
        
        mocker = VirtualenvModuleMocker(modules_to_mock, virtualenv_path)
        
        assert mocker.modules_to_mock == modules_to_mock
        assert mocker.virtualenv_path == virtualenv_path
    
    @patch('glob.glob')
    @patch('os.path.exists')
    def test_get_collection_paths_with_venv(self, mock_exists, mock_glob):
        """Test _get_collection_paths with virtual environment"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        virtualenv_path = "/path/to/venv"
        
        # Mock the virtual environment structure
        mock_exists.return_value = True
        mock_glob.return_value = ["/path/to/venv/lib/python3.9"]
        
        mocker = VirtualenvModuleMocker(modules_to_mock, virtualenv_path)
        
        with patch.object(mocker.__class__.__bases__[0], '_get_collection_paths', return_value=['/system/path']):
            paths = mocker._get_collection_paths()
        
        # Should prioritize virtual environment paths
        assert '/path/to/venv/lib/python3.9/site-packages' in paths
        assert '/path/to/venv/lib/python3.9/site-packages/ansible_collections' in paths
        assert '/system/path' in paths
        
        # Virtual environment paths should come first
        venv_path_index = paths.index('/path/to/venv/lib/python3.9/site-packages')
        system_path_index = paths.index('/system/path')
        assert venv_path_index < system_path_index
    
    @patch('os.path.exists')
    def test_get_collection_paths_no_venv(self, mock_exists):
        """Test _get_collection_paths when virtual environment doesn't exist"""
        modules_to_mock = {"test.module": "/path/to/mock"}
        virtualenv_path = "/nonexistent/venv"
        
        mock_exists.return_value = False
        
        mocker = VirtualenvModuleMocker(modules_to_mock, virtualenv_path)
        
        with patch.object(mocker.__class__.__bases__[0], '_get_collection_paths', return_value=['/system/path']):
            paths = mocker._get_collection_paths()
        
        # Should only return system paths
        assert paths == ['/system/path']
