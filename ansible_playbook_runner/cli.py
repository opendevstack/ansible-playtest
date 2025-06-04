"""
Ansible Playbook Runner CLI
================================
This script provides a command-line interface to run Ansible playbooks in a temporary virtual
environment.
It allows users to specify various options such as inventory files, extra variables, tags,
and more.
It also handles the creation of a temporary directory for the virtual environment and cleans
it up after execution, unless specified otherwise.
"""

import os
import sys
import subprocess

from typing import Optional, List

import click


from ansible_playbook_runner.utils import (
    validate_playbook,
    parse_extra_vars,
    format_ansible_result,
    create_temp_directory,
)

# Import our centralized logger
from ansible_playtest.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


@click.command()
@click.argument("playbook", type=click.Path(exists=True))
@click.option(
    "--inventory", "-i", type=click.Path(exists=True), help="Path to inventory file"
)
@click.option(
    "--extra-vars",
    "-e",
    multiple=True,
    help="Extra variables to pass to Ansible (key=value format)",
)
@click.option(
    "--private-data-dir",
    "-d",
    type=click.Path(exists=True),
    help="Directory for Ansible private data",
)
@click.option("--tags", "-t", help="Comma-separated list of tags to run")
@click.option("--skip-tags", "-T", help="Comma-separated list of tags to skip")
@click.option(
    "--verbose", "-v", count=True, help="Increase verbosity (repeat for more verbosity)"
)
@click.option(
    "--keep-temp-dir", is_flag=True, help="Keep temporary directory after execution"
)
@click.option(
    "--requirements",
    "-r",
    type=click.Path(exists=True),
    help="Path to requirements file for additional packages",
)
@click.option(
    "--use-system-python",
    is_flag=True,
    help="Use system Python instead of creating a virtualenv",
)
@click.option(
    "--collections-path",
    type=click.Path(exists=True),
    help="Path to Ansible collections directory",
)
@click.option(
    "--callback-plugins",
    multiple=True,
    type=click.Path(exists=True),
    help="Paths to callback plugins",
)
@click.option(
    "--existing-virtualenv",
    type=click.Path(exists=True),
    help="Path to an existing virtualenv to use",
)
def cli(
    playbook: str,
    inventory: Optional[str] = None,
    extra_vars: Optional[List[str]] = None,
    private_data_dir: Optional[str] = None,
    tags: Optional[str] = None,
    skip_tags: Optional[str] = None,
    verbose: int = 0,
    keep_temp_dir: bool = False,
    requirements: Optional[str] = None,
    use_system_python: bool = False,
    collections_path: Optional[str] = None,
    callback_plugins: Optional[List[str]] = None,
    existing_virtualenv: Optional[str] = None,
):
    """Run an Ansible playbook in a temporary virtual environment.

    This tool creates a temporary directory with a Python virtual environment,
    installs Ansible and ansible-runner, and runs your playbook within that environment.
    """
    temp_dir = None

    try:
        # Validate the playbook
        if not validate_playbook(playbook):
            click.echo(f"Error: Invalid playbook format: {playbook}", err=True)
            sys.exit(1)

        # Parse extra variables
        extra_vars_dict = parse_extra_vars(extra_vars) if extra_vars else {}

        # Parse tags
        tags_list = tags.split(",") if tags else None
        skip_tags_list = skip_tags.split(",") if skip_tags else None

        # Set up environment variables
        env_vars = {}

        # Add collections path if provided
        if collections_path:
            env_vars["ANSIBLE_COLLECTIONS_PATH"] = collections_path

        # Add callback plugins if provided
        if callback_plugins:
            env_vars["ANSIBLE_CALLBACK_PLUGINS"] = os.pathsep.join(callback_plugins)

        # Create a temporary directory if needed
        if not use_system_python and not existing_virtualenv:
            temp_dir = create_temp_directory()
            logger.info("Created temporary directory: %s", temp_dir)

        click.echo(
            f"Executing playbook: {click.style(os.path.basename(playbook), fg='blue')}"
        )

        # Import our API function here to avoid any import order issues
        from ansible_playbook_runner.ansible_runner_api import run_playbook

        # Run the playbook with the API
        playbook_result = run_playbook(
            playbook_path=playbook,
            inventory_path=inventory,
            extra_vars=extra_vars_dict,
            private_data_dir=private_data_dir,
            tags=tags_list,
            skip_tags=skip_tags_list,
            verbosity=verbose,
            virtualenv_path=existing_virtualenv,
            requirements=requirements,
            env_vars=env_vars,
            use_virtualenv=not use_system_python,
            keep_virtualenv=keep_temp_dir,
            collections_path=collections_path,
            callback_plugins=callback_plugins,
        )

        # Format and display the result
        formatted_result = format_ansible_result(playbook_result)
        click.echo(formatted_result)

        # Return the proper exit code
        if not playbook_result.get("success", False):
            sys.exit(playbook_result.get("rc", 1))

    except click.Abort:
        logger.info("Operation aborted by user")
        click.echo("Operation aborted by user", err=True)
        sys.exit(130)  # Standard exit code for SIGINT

    except ImportError as e:
        logger.exception("Import error: %s", e)
        click.echo(f"Error: Required package not found - {str(e)}", err=True)
        click.echo(
            "Make sure all required packages are installed in your development environment.",
            err=True,
        )
        sys.exit(1)

    except subprocess.SubprocessError as e:
        logger.exception("Subprocess error: %s", e)
        click.echo(f"Error: Failed to execute subprocess - {str(e)}", err=True)
        sys.exit(1)

    except Exception as e:
        logger.exception("Error during execution: %s", e)
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

    finally:
        # Clean up the temporary directory
        if temp_dir and not keep_temp_dir:
            try:
                import shutil

                logger.info("Cleaning up temporary directory: %s", temp_dir)
                shutil.rmtree(temp_dir)
                logger.info("Removed temporary directory: %s", temp_dir)
            except Exception as e:
                logger.warning(
                    "Failed to remove temporary directory %s: %s", temp_dir, e
                )
                click.echo(
                    f"Warning: Failed to remove temporary directory {temp_dir}: {str(e)}",
                    err=True,
                )
        elif temp_dir and keep_temp_dir:
            click.echo(
                f"Temporary directory kept at: {click.style(temp_dir, fg='yellow')}"
            )
            click.echo("You can manually remove this directory when you're done.")


if __name__ == "__main__":
    cli("")
