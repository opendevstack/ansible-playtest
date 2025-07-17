import pytest
from ansible_playtest.ansible_mocker.module_mocker import ModuleMocker
from typing import Dict, Optional
import os


class VirtualenvAwareModuleMocker:
    """
    Wrapper around ModuleMocker that handles virtual environment scenarios.
    
    This class defers the actual mocking until the virtual environment is ready,
    ensuring that mocks are applied to the correct Ansible installation.
    """
    
    def __init__(self, modules_to_mock: Dict[str, str]):
        self.modules_to_mock = modules_to_mock
        self.mocker = None
        self.is_active = False
        
    def setup_mocks(self, virtualenv_path: Optional[str] = None):
        """
        Set up the mocks, optionally targeting a specific virtual environment.
        
        Args:
            virtualenv_path: Path to the virtual environment. If provided,
                           mocks will be applied to the virtualenv's Ansible installation.
        """
        if not self.modules_to_mock:
            return
            
        if virtualenv_path:
            # Create a specialized ModuleMocker for the virtual environment
            self.mocker = VirtualenvModuleMocker(self.modules_to_mock, virtualenv_path)
        else:
            # Use standard ModuleMocker for system-wide installation
            self.mocker = ModuleMocker(self.modules_to_mock)
            
        self.mocker.setup_mocks()
        self.is_active = True
        
    def restore_mocks(self):
        """Restore original modules if mocks are active."""
        if self.is_active and self.mocker:
            self.mocker.restore_modules()
            self.is_active = False
            
    def __enter__(self):
        # Don't setup mocks immediately - wait for explicit call
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.restore_mocks()


class VirtualenvModuleMocker(ModuleMocker):
    """
    ModuleMocker that operates within a virtual environment.
    """
    
    def __init__(self, modules_to_mock: Dict[str, str], virtualenv_path: str):
        super().__init__(modules_to_mock)
        self.virtualenv_path = virtualenv_path
        
    def _get_collection_paths(self):
        """
        Override to prioritize virtual environment paths.
        """
        # Get the original paths
        paths = super()._get_collection_paths()
        
        # Prepend virtual environment paths
        venv_paths = []
        
        if self.virtualenv_path and os.path.exists(self.virtualenv_path):
            # Add virtual environment site-packages
            # Handle different Python versions by checking common locations
            import glob
            python_dirs = glob.glob(os.path.join(self.virtualenv_path, "lib", "python*"))
            
            for python_dir in python_dirs:
                site_packages = os.path.join(python_dir, "site-packages")
                if os.path.exists(site_packages):
                    venv_paths.append(site_packages)
                    venv_paths.append(os.path.join(site_packages, "ansible_collections"))
        
        # Prioritize virtual environment paths
        return venv_paths + paths


@pytest.fixture
def module_mocker(request):
    """
    Fixture to mock Ansible modules during test execution.
    
    This fixture now works correctly with virtual environments by deferring
    the actual mocking until the virtual environment is set up.
    
    Configure by setting the 'modules_to_mock' marker on the test function.
    Example:
    
    @pytest.mark.modules_to_mock({
        "community.general.file_size": "/path/to/mock/file_size.py"
    })
    def test_with_mocked_modules(module_mocker):
        # Test code that uses the mocked modules
        pass
    """
    marker = request.node.get_closest_marker("modules_to_mock")
    modules_to_mock = {}
    
    if marker:
        modules_to_mock = marker.args[0] if marker.args else {}
    
    with VirtualenvAwareModuleMocker(modules_to_mock) as mocker:
        yield mocker


def pytest_configure(config):
    """Add the 'modules_to_mock' marker to pytest."""
    config.addinivalue_line(
        "markers", 
        "modules_to_mock(dict): dictionary of Ansible modules to mock: {module_name: mock_path}"
    )