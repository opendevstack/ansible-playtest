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


def _default_output() -> Dict[str, Any]:
    """Return the default output dictionary for playbook execution."""
    return {
        "status": "successful",
        "rc": 0,
        "success": True,
        "stats": {},
    }


def _prepare_env(
    env_vars: Optional[Dict[str, str]],
    collections_path: Optional[str],
    callback_plugins: Optional[List[str]],
) -> Dict[str, str]:
    """Prepare the environment variables for playbook execution."""
    cmd_env = os.environ.copy()
    if env_vars:
        cmd_env.update(env_vars)
    if collections_path:
        cmd_env["ANSIBLE_COLLECTIONS_PATH"] = collections_path
    if callback_plugins:
        cmd_env["ANSIBLE_CALLBACK_PLUGINS"] = os.pathsep.join(callback_plugins)
    return cmd_env


def _build_run_options(
    playbook_path: str,
    inventory_path: Optional[str],
    extra_vars: Optional[Dict[str, Any]],
    private_data_dir: Optional[str],
    tags: Optional[List[str]],
    skip_tags: Optional[List[str]],
    verbosity: int,
) -> Dict[str, Any]:
    """Build the run options dictionary for ansible_runner.run."""
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
    return run_options


def _setup_virtualenv(virtualenv_path: Optional[str]):
    """Set up a virtual environment and return (temp_dir, venv)."""
    if not virtualenv_path:
        temp_dir = tempfile.mkdtemp(prefix="ansible_runner_")
        venv = VirtualEnvironment(temp_dir)
        venv.create(install_playtest=True)
    else:
        temp_dir = None
        venv = VirtualEnvironment(
            base_dir=os.path.dirname(virtualenv_path),
            name=os.path.basename(virtualenv_path),
            created=True,
        )
    return temp_dir, venv


def _install_requirements(venv, requirements):
    """Install requirements into the virtual environment if provided."""
    if not venv or not requirements:
        return
    if isinstance(requirements, str) and os.path.isfile(requirements):
        venv.install_requirements(requirements)
    elif isinstance(requirements, list):
        venv.install_packages(requirements)


def _parse_virtualenv_result(cmd_result) -> Dict[str, Any]:
    """Parse the result of running the playbook in a virtualenv."""
    if cmd_result.returncode != 0:
        logging.error(
            "Playbook execution failed with return code: %s",
            cmd_result.returncode,
        )
        logging.error("Error: %s", cmd_result.stderr)
        return {
            "status": "failed",
            "rc": cmd_result.returncode,
            "success": False,
            "stats": {},
            "error": cmd_result.stderr,
        }
    return _default_output()


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

    temp_dir = None
    venv = None
    output = _default_output()
    logger.info("Running playbook: %s", playbook_path)

    try:
        cmd_env = _prepare_env(env_vars, collections_path, callback_plugins)
        run_options = _build_run_options(
            playbook_path,
            inventory_path,
            extra_vars,
            private_data_dir,
            tags,
            skip_tags,
            verbosity,
        )

        if use_virtualenv:
            temp_dir, venv = _setup_virtualenv(virtualenv_path)
            _install_requirements(venv, requirements)
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
            cmd_result = venv.run_command(script, cmd_env)
            output = _parse_virtualenv_result(cmd_result)
        else:
            if env_vars:
                run_options["envvars"] = env_vars
            if private_data_dir and not os.path.exists(private_data_dir):
                os.makedirs(private_data_dir, exist_ok=True)
            result: Any = ansible_runner.run(**run_options)
            logger.info("Playbook execution completed with result: %s", result)
            output = {
                "status": result.status,
                "rc": result.rc,
                "success": result.status == "successful",
                "stats": getattr(result, "stats", {}),
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
