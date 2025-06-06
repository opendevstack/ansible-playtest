import os
import tempfile
import subprocess
import pytest
import shutil
from ansible_playbook_runner.environment import create_virtual_environment, install_packages, VirtualEnvironment

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

    def test_ansible_playtest_installation(self, temp_dir):
        """Test that ansible_playtest is installed with the mock servers available."""
        # Create a virtual environment with ansible_playtest installed
        venv_path = create_virtual_environment(temp_dir, install_playtest=True)
        
        # Verify that we can import the mock servers and other components
        python_cmd = os.path.join(venv_path, 'bin', 'python')
        
        # Print Python path to help with debugging
        debug_result = subprocess.run(
            [python_cmd, '-c', 'import sys; print("Python path:"); [print(p) for p in sys.path]'],
            capture_output=True,
            text=True
        )
        print(f"Python path debug:\n{debug_result.stdout}")
        
        # List installed packages
        debug_result = subprocess.run(
            [os.path.join(venv_path, 'bin', 'pip'), 'list'],
            capture_output=True,
            text=True
        )
        print(f"Installed packages:\n{debug_result.stdout}")
        
        # Try to import the ansible_playtest package first
        result = subprocess.run(
            [python_cmd, '-c', 'import ansible_playtest; print(f"ansible_playtest package found at {ansible_playtest.__file__}")'],
            capture_output=True,
            text=True
        )
        
        print(f"Import ansible_playtest result stdout: {result.stdout}")
        print(f"Import ansible_playtest result stderr: {result.stderr}")
        
        # Now try to import the mock SMTP server
        result = subprocess.run(
            [python_cmd, '-c', 'from ansible_playtest.mocks_servers import mock_smtp_server; print("Success!")'],
            capture_output=True,
            text=True
        )
        
        print(f"Import mock_smtp_server result stdout: {result.stdout}")
        print(f"Import mock_smtp_server result stderr: {result.stderr}")
        
        # Even if we get an error, let's continue to see what's in the mocks_servers dir
        subprocess.run(
            [python_cmd, '-c', 
             'import os, sys; import ansible_playtest; ' +
             'mocks_dir = os.path.join(os.path.dirname(ansible_playtest.__file__), "mocks_servers"); ' +
             'print(f"Contents of {mocks_dir}: {os.listdir(mocks_dir) if os.path.exists(mocks_dir) else \'directory not found\'}")'],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Failed to import mock_smtp_server: {result.stderr}"
        assert "Success!" in result.stdout

class TestVirtualEnvironment:
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
    
    def test_venv_create_with_playtest(self, temp_dir):
        """Test creating a virtual environment with ansible_playtest installed."""
        venv = VirtualEnvironment(temp_dir)
        venv.create(install_playtest=True)
        
        # Print Python path to help with debugging
        debug_result = subprocess.run(
            [venv.python_path, '-c', 'import sys; print("Python path:"); [print(p) for p in sys.path]'],
            capture_output=True,
            text=True
        )
        print(f"Python path debug:\n{debug_result.stdout}")
        
        # List installed packages
        debug_result = subprocess.run(
            [venv.pip_path, 'list'],
            capture_output=True,
            text=True
        )
        print(f"Installed packages:\n{debug_result.stdout}")
        
        # Check if ansible_playtest directory exists
        result = subprocess.run(
            [venv.python_path, '-c', 
             'import os, sys; print("ansible_playtest directories found:"); [print(p) for p in sys.path if os.path.exists(os.path.join(p, "ansible_playtest"))]'],
            capture_output=True,
            text=True
        )
        print(f"ansible_playtest directories search:\n{result.stdout}")
        
        # Verify that the mock servers are available
        result = subprocess.run(
            [venv.python_path, '-c', 
             'from ansible_playtest.mocks_servers import mock_smtp_server; print("Mock server imported!")'],
            capture_output=True,
            text=True
        )
        
        print(f"Import result stdout: {result.stdout}")
        print(f"Import result stderr: {result.stderr}")
        
        assert result.returncode == 0, f"Failed to import mock_smtp_server: {result.stderr}"
        assert "Mock server imported!" in result.stdout
        
    def test_install_ansible_playtest_method(self, temp_dir):
        """Test the install_ansible_playtest method."""
        venv = VirtualEnvironment(temp_dir)
        venv.create()
        venv.install_ansible_playtest()
        
        # Check Python paths
        debug_result = subprocess.run(
            [venv.python_path, '-c', 'import sys; print("Python path:"); [print(p) for p in sys.path]'],
            capture_output=True,
            text=True
        )
        print(f"Python path debug:\n{debug_result.stdout}")
        
        # Verify that the ansible_playtest package is installed
        result = subprocess.run(
            [venv.python_path, '-c', 
             'import ansible_playtest; print(f"ansible_playtest imported successfully")'],
            capture_output=True,
            text=True
        )
        
        print(f"Import result stdout: {result.stdout}")
        print(f"Import result stderr: {result.stderr}")
        
        assert result.returncode == 0, f"Failed to import ansible_playtest: {result.stderr}"
        assert "ansible_playtest imported successfully" in result.stdout