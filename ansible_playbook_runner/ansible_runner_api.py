"""
Functions for running Ansible playbooks using the ansible-runner API.
"""

import os
import logging  # Keep this for log levels
import json
import tempfile
import sys
from typing import Optional, Dict, List, Any, Union

# Try importing ansible_runner - we'll handle the ImportError in run_playbook
try:
    import ansible_runner
except ImportError:
    ansible_runner = None

from ansible_playbook_runner.environment import VirtualEnvironment
from ansible_playtest.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


def run_playbook(
    playbook_path: str,
    inventory_path: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    private_data_dir: Optional[str] = None,
    tags: Optional[List[str]] = None,
    skip_tags: Optional[List[str]] = None,
    verbosity: int = 0,
    virtualenv_path: Optional[str] = None,
    requirements: Optional[Union[str, List[str]]] = None,
    env_vars: Optional[Dict[str, str]] = None,
    use_virtualenv: bool = False,
    keep_virtualenv: bool = False,
    collections_path: Optional[str] = None,
    callback_plugins: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Run an Ansible playbook using the Ansible Runner API.

    Note: This function imports ansible_runner at runtime to ensure it uses
    the version installed in the virtual environment.

    Args:
        playbook_path (str): The path to the Ansible playbook to run.
        inventory_path (str, optional): The path to the inventory file.
        extra_vars (dict, optional): Extra variables to pass to the playbook.
        private_data_dir (str, optional): The directory for private data.
        tags (list, optional): Tags to run.
        skip_tags (list, optional): Tags to skip.
        verbosity (int, optional): Verbosity level (0-5).
        virtualenv_path (str, optional): Path to an existing virtual environment.
        requirements (str or list, optional): Path to requirements file or list of packages to install.
        env_vars (dict, optional): Environment variables to set during playbook execution.
        use_virtualenv (bool): Whether to use a temporary virtualenv (True) or current environment (False).
        keep_virtualenv (bool): Whether to keep the temporary virtualenv after execution.
        collections_path (str, optional): Path to Ansible collections.
        callback_plugins (list, optional): List of paths to Ansible callback plugins.

    Returns:
        dict: The result of the playbook execution.

    Raises:
        ImportError: If ansible_runner module is not available.
    """
    # Check if ansible_runner is available
    if ansible_runner is None:
        raise ImportError("ansible_runner is required to run playbooks")

    # Create a temp dir if using virtualenv and no path provided
    temp_dir = None
    venv = None
    output = {
        "status": "successful",  # Fix typo in "successful"
        "rc": 0,
        "success": True,
        "stats": {},  # Always include stats key, even if empty
    }

    logger.info("Running playbook: %s", playbook_path)

    try:
        # Set up the environment
        cmd_env = os.environ.copy()
        if env_vars:
            cmd_env.update(env_vars)

        # Set up Ansible environment variables
        if collections_path:
            cmd_env["ANSIBLE_COLLECTIONS_PATH"] = collections_path

        if callback_plugins:
            cmd_env["ANSIBLE_CALLBACK_PLUGINS"] = os.pathsep.join(callback_plugins)

        # Log what we're about to do
        logger.info("Running playbook: %s", playbook_path)
        if inventory_path:
            logger.info("Using inventory: %s", inventory_path)

        # Build run options - consistent for both virtualenv and non-virtualenv paths
        run_options = {"playbook": playbook_path, "verbosity": verbosity}

        if inventory_path:
            run_options["inventory"] = inventory_path

        if extra_vars:
            run_options["extravars"] = extra_vars

        if private_data_dir:
            run_options["private_data_dir"] = private_data_dir

        if tags:
            run_options["tags"] = tags

        if skip_tags:
            run_options["skip_tags"] = skip_tags

        # Handle virtualenv setup if needed
        if use_virtualenv:
            if not virtualenv_path:
                # Create a temporary directory
                temp_dir = tempfile.mkdtemp(prefix="ansible_runner_")
                venv = VirtualEnvironment(temp_dir)
                venv.create()
            else:
                # Use the provided virtualenv path
                venv = VirtualEnvironment(
                    base_dir=os.path.dirname(virtualenv_path),
                    name=os.path.basename(virtualenv_path),
                    created=True,
                )


            # Install additional requirements
            if requirements:
                if isinstance(requirements, str) and os.path.isfile(requirements):
                    venv.install_requirements(requirements)
                elif isinstance(requirements, list):
                    venv.install_packages(requirements)

            # We can't directly use ansible_runner in the virtualenv from our code
            # So we need to execute a script that does the import and runs the playbook
            script = [
                "-c",
                _generate_runner_script(
                    playbook_path,
                    inventory_path,
                    extra_vars,
                    private_data_dir,
                    tags,
                    skip_tags,
                    verbosity,
                ),
            ]

            # Run the command in the virtualenv
            cmd_result = venv.run_command(script, cmd_env)

            # Parse the result
            if cmd_result.returncode != 0:
                logging.error(
                    "Playbook execution failed with return code: %s",
                    cmd_result.returncode,
                )
                logging.error("Error: %s", cmd_result.stderr)
                output = {
                    "status": "failed",
                    "rc": cmd_result.returncode,
                    "success": False,
                    "stats": {},
                    "error": cmd_result.stderr,
                }

        else:
            # When not using virtualenv, we can directly use the ansible_runner module
            # Set environment variables if provided
            if env_vars:
                run_options["envvars"] = env_vars

            # Ensure private_data_dir exists if specified
            if private_data_dir and not os.path.exists(private_data_dir):
                os.makedirs(private_data_dir, exist_ok=True)

            # Using Any type for now - the type checker doesn't recognize ansible_runner.RunnerConfig type
            result: Any = ansible_runner.run(**run_options)
            logger.info("Playbook execution completed with result: %s", result)

            # Prepare the result dictionary
            output = {
                "status": result.status,
                "rc": result.rc,
                "success": result.status == "successful",
                "stats": getattr(result, "stats", {}),  # Include stats if available
            }

        if output.get("success", False):
            logger.info("Playbook executed successfully.")
        else:
            logger.error(
                "Playbook execution failed with status: %s",
                output.get("status", "unknown"),
            )
            logger.error("Return code: %s", output.get("rc", "unknown"))

        return output

    finally:
        # Clean up temporary resources
        if temp_dir and venv and not keep_virtualenv:
            venv.cleanup()
            try:
                os.rmdir(temp_dir)
            except OSError as e:
                logger.warning("Failed to remove temporary directory: %s", e)


def _generate_runner_script(
    playbook_path: str,
    inventory_path: Optional[str] = None,
    extra_vars: Optional[Dict[str, Any]] = None,
    private_data_dir: Optional[str] = None,
    tags: Optional[List[str]] = None,
    skip_tags: Optional[List[str]] = None,
    verbosity: int = 0,
) -> str:
    """Generate a Python script to run ansible_runner in a subprocess."""
    script = f"""
import json
import sys
import os
import ansible_runner

# Build run options
run_options = {{
    "playbook": "{playbook_path}",
    "verbosity": {verbosity}
}}

{f'run_options["inventory"] = "{inventory_path}"' if inventory_path else ''}
{f'run_options["extravars"] = {json.dumps(extra_vars)}' if extra_vars else ''}
{f'run_options["private_data_dir"] = "{private_data_dir}"' if private_data_dir else ''}
{f'run_options["tags"] = {json.dumps(tags)}' if tags else ''}
{f'run_options["skip_tags"] = {json.dumps(skip_tags)}' if skip_tags else ''}

# Run the playbook
result = ansible_runner.run(**run_options)

# Check the result and exit accordingly
if result.status != "successful":
    sys.exit(1)  # Exit with a non-zero status code to indicate failure
sys.exit(0)  # Exit with a zero status code to indicate success
"""
    return script
