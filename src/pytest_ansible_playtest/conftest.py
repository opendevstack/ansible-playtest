"""
Pytest configuration for Ansible tests
"""
import os
import sys
import pytest

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

@pytest.fixture(scope="session", autouse=True)
def setup_ansible_environment():
    """
    Set up the environment variables for Ansible tests.
    This ensures that our mock module tracker callback is correctly loaded.
    """
    # Store original environment
    original_env = os.environ.copy()
    
    # Set up the environment for all tests
    os.environ['ANSIBLE_CONFIG'] = os.path.join(os.path.dirname(__file__), 'ansible-test.cfg')
    
    # Set the callback plugins path explicitly
    callback_plugins_path = os.path.abspath(os.path.join(project_root, 'callback_plugins'))
    os.environ['ANSIBLE_CALLBACK_PLUGINS'] = callback_plugins_path
    os.environ['ANSIBLE_CALLBACKS_ENABLED'] = 'mock_module_tracker'
    
    # Let the test run
    yield
    
    # Restore the original environment when done
    os.environ.clear()
    os.environ.update(original_env)