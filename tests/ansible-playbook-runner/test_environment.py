import os
import tempfile
import subprocess
import pytest
import shutil
from ansible_playbook_runner.environment import create_virtual_environment, install_packages

class TestEnvironment:
    @pytest.fixture
    def temp_dir(self):
        """Fixture to create a temporary directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except (OSError, IOError) as e:
            print(f"Error cleaning up temporary directory: {e}")

    def test_virtual_environment_creation(self, temp_dir):
        """Test that the virtual environment is created successfully."""
        venv_path = create_virtual_environment(temp_dir)
        
        # Check that the virtual environment directory exists
        assert os.path.exists(venv_path)
        
        # Check for essential virtual environment files
        assert os.path.exists(os.path.join(venv_path, 'bin', 'python'))
        assert os.path.exists(os.path.join(venv_path, 'bin', 'pip'))
        assert os.path.exists(os.path.join(venv_path, 'bin', 'activate'))
        
        # Check that the virtual environment can be activated and used
        activate_script = os.path.join(venv_path, 'bin', 'python')
        result = subprocess.run(
            [activate_script, '-c', 'import sys; print(sys.executable)'],
            capture_output=True, 
            text=True
        )
        
        # The executable path should be from our virtual environment
        assert venv_path in result.stdout
        assert result.returncode == 0

    def test_package_installation(self, temp_dir):
        """Test that packages can be installed in the virtual environment."""
        venv_path = create_virtual_environment(temp_dir)
        
        # Install a simple test package
        install_packages(venv_path, ['pytest'])
        
        # Check if the package was installed
        python_path = os.path.join(venv_path, 'bin', 'python')
        result = subprocess.run(
            [python_path, '-c', 'import pytest; print("Package installed")'],
            capture_output=True,
            text=True
        )
        
        assert "Package installed" in result.stdout
        assert result.returncode == 0