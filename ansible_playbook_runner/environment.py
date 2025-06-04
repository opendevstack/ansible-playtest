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
            - Command Execution: Runs commands using the virtual environment's Python interpreter.
            - Cleanup: Removes the virtual environment directory.

Legacy Functions:
    create_virtual_environment(temp_dir: str) -> str:
        Creates and returns the path to a virtual environment in the provided directory.
    install_packages(venv_dir: str, packages: list[str]) -> None:
        Installs a list of packages in an already created virtual environment.

Usage Example:
    >>> from environment import VirtualEnvironment
    >>> venv_manager = VirtualEnvironment("/path/to/project", name="venv")
    >>> venv_manager.create()
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

    def create(self) -> str:
        """
        Create the virtual environment.

        Returns:
            str: Path to the created virtual environment.
        """
        if self._created:
            return self.path

        logger.info("Creating virtual environment in %s", self.path)
        venv.create(self.path, with_pip=True)
        self._created = True
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


# Legacy functions for backward compatibility
def create_virtual_environment(temp_dir: str) -> str:
    """
    Create a Python virtual environment within the specified temporary directory.

    Args:
        temp_dir (str): The temporary directory to create the virtual environment in.

    Returns:
        str: The path to the created virtual environment.
    """
    venv_obj = VirtualEnvironment(temp_dir)
    return venv_obj.create()


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
