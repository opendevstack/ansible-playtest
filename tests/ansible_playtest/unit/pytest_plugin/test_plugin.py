"""
Unit tests for plugin.py
"""
import os
import pytest
import importlib
import ansible_playtest.ansible_callback


def test_callback_plugin_path_exists():
    """Test that we can correctly find the callback plugin directory"""
    print("\nRunning test_callback_plugin_path_exists")
    
    # Get the directory containing the ansible_callback package
    callback_dir = os.path.dirname(ansible_playtest.ansible_callback.__file__)
    print(f"Callback directory: {callback_dir}")
    
    # Verify the directory exists
    assert os.path.exists(callback_dir)
    
    # Verify the mock_module_tracker.py file exists in that directory
    plugin_path = os.path.join(callback_dir, 'mock_module_tracker.py')
    print(f"Plugin path: {plugin_path}")
    assert os.path.exists(plugin_path)
    
    print("Test completed successfully")
