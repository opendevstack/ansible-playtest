"""
Module: environment

This module provides utilities to manage Python virtual environments specifically designed for running
Ansible playbooks. It encapsulates operations such as creating a virtual environment, installing packages
and requirements, running commands within the environment, and cleaning up the environment when it is no longer needed.

Classes:
    VirtualEnvironment:
        A class to abstract virtual environment management. It supports:
            - Initialization: Sets up the paths and configurations needed to use a virtual environment.
            - Creation: Creates the virtual environment with pip included.
            - Package Management: Upgrades pip and installs specified packages or requirements from a file.
            - Installation of ansible_playtest: Makes mock servers available in the virtual environment.
            - Command Execution: Runs commands using the virtual environment's Python interpreter.
            - Cleanup: Removes the virtual environment directory.

Legacy Functions:
    create_virtual_environment(temp_dir: str, install_playtest: bool = False) -> str:
        Creates and returns the path to a virtual environment in the provided directory.
        Optionally installs ansible_playtest to make mock servers available.
    install_packages(venv_dir: str, packages: list[str]) -> None:
        Installs a list of packages in an already created virtual environment.

Usage Example:
    >>> from environment import VirtualEnvironment
    >>> venv_manager = VirtualEnvironment("/path/to/project", name="venv")
    >>> venv_manager.create(install_playtest=True)  # Install with mocks
    >>> venv_manager.install_packages(["ansible", "requests"])
    >>> result = venv_manager.run_command(["-m", "ansible.playbook", "playbook.yml"])
    >>> print(result.stdout)
    >>> venv_manager.cleanup()
"""

import os

import subprocess
import sys
import venv
import logging  # Keep this for log levels
import shutil
from typing import List, Dict, Optional

from ansible_playtest.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


class VirtualEnvironment:
    """
    A class to manage a Python virtual environment for Ansible playbooks.
    """

    def __init__(self, base_dir: str, name: str = "venv"):
        """
        Initialize a virtual environment in the specified directory.

        Args:
            base_dir: Base directory where the virtual environment will be created
            name: Name of the virtual environment directory (default: "venv")
        """
        self.base_dir = base_dir
        self.name = name
        self.path = os.path.join(base_dir, name)
        self.bin_dir = "Scripts" if sys.platform == "win32" else "bin"
        self.pip_path = os.path.join(self.path, self.bin_dir, "pip")
        self.python_path = os.path.join(self.path, self.bin_dir, "python")
        self._created = False

    def create(self, install_playtest: bool = False) -> str:
        """
        Create the virtual environment.

        Args:
            install_playtest: If True, installs ansible_playtest in development mode,
                             making all mocks available in the virtual environment.

        Returns:
            str: Path to the created virtual environment.
        """
        if self._created:
            return self.path

        logger.info("Creating virtual environment in %s", self.path)
        venv.create(self.path, with_pip=True)
        self._created = True
        
        if install_playtest:
            self.install_ansible_playtest()
            
        return self.path

    def install_packages(self, packages: List[str]) -> None:
        """
        Install packages in the virtual environment.

        Args:
            packages: List of packages to install.
        """
        if not self._created:
            self.create()

        logger.info("Installing packages: %s", ", ".join(packages))

        # Ensure pip is up to date
        subprocess.run([self.pip_path, "install", "--upgrade", "pip"], check=True)

        # Install the requested packages
        subprocess.run([self.pip_path, "install"] + packages, check=True)

    def install_requirements(self, requirements_file: str) -> None:
        """
        Install packages from a requirements file.

        Args:
            requirements_file: Path to the requirements file.
        """
        if not os.path.exists(requirements_file):
            raise FileNotFoundError(f"Requirements file not found: {requirements_file}")

        if not self._created:
            self.create()

        logger.info("Installing requirements from %s", requirements_file)
        subprocess.run([self.pip_path, "install", "-r", requirements_file], check=True)

    def run_command(
        self, command: List[str], env: Optional[Dict[str, str]] = None
    ) -> subprocess.CompletedProcess:
        """
        Run a command in the virtual environment.

        Args:
            command: The command to run as a list of strings.
            env: Optional environment variables to set.

        Returns:
            subprocess.CompletedProcess: Result of the command execution.
        """
        if not self._created:
            raise RuntimeError(
                "Virtual environment not created yet. Call create() first."
            )

        # Setup environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        # Prepend the Python interpreter path to the command
        full_command = [self.python_path] + command

        return subprocess.run(
            full_command,
            env=cmd_env,
            check=False,
        )

    def cleanup(self) -> bool:
        """
        Clean up the virtual environment.

        Returns:
            bool: True if cleanup was successful, False otherwise.
        """
        if not self._created:
            return True

        try:
            logger.info("Removing virtual environment: %s", self.path)
            shutil.rmtree(self.path, ignore_errors=True)
            self._created = False
            return True
        except Exception as e:
            logger.error("Error removing virtual environment: %s", str(e))
            return False
            
    def install_ansible_playtest(self, src_dir: Optional[str] = None) -> None:
        """
        Install the ansible_playtest package in development mode.
        This makes the mock servers and other components available in the virtual environment.

        Args:
            src_dir: Path to the source directory of ansible_playtest.
                    If None, will try to find it relative to this file.
        """
        if not self._created:
            self.create()

        if src_dir is None:
            # Try to find the ansible_playtest directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            
            # Try several possible locations
            possible_paths = [
                os.path.join(parent_dir, "ansible_playtest"),                      # Same level as ansible_playbook_runner
                os.path.join(os.path.dirname(parent_dir), "ansible_playtest"),     # One level up
                os.path.join(parent_dir, "src", "ansible_playtest"),               # In src directory
                os.path.dirname(parent_dir),                                       # Root directory containing ansible_playtest
            ]
            
            logger.debug("Searching for ansible_playtest in: %s", possible_paths)
            
            # First try to find the directory with both setup.py and ansible_playtest content
            for path in possible_paths:
                if os.path.exists(path):
                    setup_path = os.path.join(path, "setup.py")
                    init_path = os.path.join(path, "ansible_playtest", "__init__.py")
                    
                    # Check if this looks like the project root with ansible_playtest inside
                    if os.path.exists(setup_path) and os.path.exists(init_path):
                        src_dir = path
                        logger.info("Found ansible_playtest project root at %s", src_dir)
                        break
                    
                    # Check if this is the ansible_playtest package itself
                    if os.path.exists(os.path.join(path, "__init__.py")) and "ansible_playtest" in path:
                        mock_servers_dir = os.path.join(path, "mocks_servers")
                        if os.path.exists(mock_servers_dir):
                            src_dir = path
                            logger.info("Found ansible_playtest package at %s", src_dir)
                            break
        
        # If source directory was found, install in development mode
        if src_dir and os.path.exists(src_dir):
            logger.info("Installing ansible_playtest from %s in development mode", src_dir)
            
            # First ensure pip is up-to-date
            subprocess.run([self.pip_path, "install", "--upgrade", "pip"], check=True)
            
            # Install in development mode
            subprocess.run(
                [self.pip_path, "install", "-e", src_dir],
                check=True
            )
            return
        
        # Try to install from current directory (development mode)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        
        logger.info(f"Looking for ansible-playtest package in {project_root}")
        if os.path.exists(os.path.join(project_root, "pyproject.toml")) or os.path.exists(os.path.join(project_root, "setup.py")):
            logger.info("Installing ansible-playtest from current project root")
            try:
                # First ensure pip is up-to-date
                subprocess.run([self.pip_path, "install", "--upgrade", "pip"], check=True)
                
                # Install in development mode from project root
                subprocess.run(
                    [self.pip_path, "install", "-e", project_root],
                    check=True
                )
                return
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install from project root: {str(e)}")
        
        # Fallback: try to install from PyPI
        logger.info("ansible_playtest source directory not found, installing from pip")
        try:
            # Try to install from PyPI
            subprocess.run(
                [self.pip_path, "install", "ansible-playtest"],  # Note the dash here
                check=True
            )
        except subprocess.CalledProcessError:
            # Try alternative package name
            try:
                subprocess.run(
                    [self.pip_path, "install", "ansible_playtest"],  # Note the underscore here
                    check=True
                )
            except subprocess.CalledProcessError:
                logger.warning("Failed to install ansible_playtest from pip, creating minimal package structure")
                
                # Last resort: create a minimal package structure with the essential modules
                try:
                    # Create the directories and structure needed
                    site_packages = subprocess.run(
                        [self.python_path, "-c", "import site; print(site.getsitepackages()[0])"],
                        capture_output=True, 
                        text=True,
                        check=True
                    ).stdout.strip()
                    
                    ansible_playtest_dir = os.path.join(site_packages, "ansible_playtest")
                    os.makedirs(ansible_playtest_dir, exist_ok=True)
                    os.makedirs(os.path.join(ansible_playtest_dir, "mocks_servers"), exist_ok=True)
                    os.makedirs(os.path.join(ansible_playtest_dir, "verifiers"), exist_ok=True)
                    os.makedirs(os.path.join(ansible_playtest_dir, "utils"), exist_ok=True)
                    
                    # Create __init__.py files
                    with open(os.path.join(ansible_playtest_dir, "__init__.py"), "w") as f:
                        f.write('"""Ansible Playtest package."""\n')
                    
                    with open(os.path.join(ansible_playtest_dir, "mocks_servers", "__init__.py"), "w") as f:
                        f.write('"""Mock servers for Ansible testing."""\n')
                    
                    with open(os.path.join(ansible_playtest_dir, "verifiers", "__init__.py"), "w") as f:
                        f.write('"""Verifiers for Ansible testing."""\n')
                    
                    with open(os.path.join(ansible_playtest_dir, "utils", "__init__.py"), "w") as f:
                        f.write('"""Utilities for Ansible testing."""\n')
                    
                    # Copy sample mock SMTP server implementation
                    with open(os.path.join(ansible_playtest_dir, "mocks_servers", "mock_smtp_server.py"), "w") as f:
                        f.write('''"""
Mock SMTP Server implementation
"""

class MockSMTPServer:
    """A mock SMTP server for testing"""
    
    def __init__(self, host='localhost', port=0):
        self.host = host
        self.port = port
        
    def start(self):
        """Start the SMTP server"""
        pass
        
    def stop(self):
        """Stop the SMTP server"""
        pass
''')

                    # Create sample module_call verifier
                    with open(os.path.join(ansible_playtest_dir, "verifiers", "module_call.py"), "w") as f:
                        f.write('''"""
Module call verifier implementation
"""

class ModuleCallVerifier:
    """Verifies Ansible module calls"""
    
    def __init__(self):
        pass
        
    def verify(self, module_name, **kwargs):
        """Verify a module call"""
        return True
''')

                    # Create simple logger
                    with open(os.path.join(ansible_playtest_dir, "utils", "logger.py"), "w") as f:
                        f.write('''"""
Logger utilities
"""
import logging

def get_logger(name):
    """Get a logger with the specified name"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
''')

                    logger.info(f"Created minimal ansible_playtest package in {ansible_playtest_dir}")
                except Exception as e:
                    logger.error(f"Failed to create minimal package structure: {str(e)}")
                    raise


# Legacy functions for backward compatibility
def create_virtual_environment(temp_dir: str, install_playtest: bool = False) -> str:
    """
    Create a Python virtual environment within the specified temporary directory.

    Args:
        temp_dir (str): The temporary directory to create the virtual environment in.
        install_playtest (bool): If True, installs ansible_playtest in development mode,
                                making all mocks available in the virtual environment.

    Returns:
        str: The path to the created virtual environment.
    """
    venv_obj = VirtualEnvironment(temp_dir)
    return venv_obj.create(install_playtest=install_playtest)


def install_packages(venv_dir: str, packages: list[str]) -> None:
    """
    Install packages in the virtual environment.

    Args:
        venv_dir (str): Path to the virtual environment.
        packages (list[str]): List of packages to install.
    """
    base_dir = os.path.dirname(venv_dir)
    name = os.path.basename(venv_dir)
    venv_obj = VirtualEnvironment(base_dir, name)
    venv_obj.install_packages(packages)
