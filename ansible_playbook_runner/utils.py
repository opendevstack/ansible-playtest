import os
import yaml
import json
import shlex
import logging  # Keep this for log levels
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union

from ansible_playtest.utils.logger import get_logger

# Get logger for this module
logger = get_logger(__name__)


def create_temp_directory() -> str:
    """
    Creates a temporary directory and returns its path.

    Returns:
        str: Path to the created temporary directory
    """
    temp_dir = tempfile.mkdtemp(prefix="ansible-runner-")
    logger.info(f"Temporary directory created at: {temp_dir}")
    return temp_dir


def sanitize_input(user_input: str) -> str:
    """
    Sanitizes user input to prevent injection attacks.

    Args:
        user_input (str): The input string to sanitize

    Returns:
        str: Sanitized input string
    """
    sanitized_input = shlex.quote(user_input)
    return sanitized_input


def parse_extra_vars(extra_vars_list: List[str]) -> Dict[str, Any]:
    """
    Parse extra variables from command line arguments.

    Args:
        extra_vars_list (List[str]): List of extra vars in the format key=value

    Returns:
        Dict[str, Any]: Dictionary of parsed extra vars
    """
    result = {}
    for var in extra_vars_list:
        if "=" in var:
            key, value = var.split("=", 1)
            # Try to detect and convert value types
            parsed_value = parse_value(value.strip())
            result[key.strip()] = parsed_value
        else:
            logger.warning(f"Ignoring invalid extra var format: {var}")
    return result


def parse_value(value: str) -> Any:
    """
    Try to parse a string value into its appropriate Python type.

    Args:
        value (str): String value to parse

    Returns:
        Any: Parsed value as the appropriate type
    """
    # Handle booleans
    if value.lower() in ("true", "yes"):
        return True
    if value.lower() in ("false", "no"):
        return False

    # Handle null/None
    if value.lower() in ("null", "none"):
        return None

    # Handle numbers
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        # It's a string, leave as is
        return value


def validate_playbook(playbook_path: str) -> bool:
    """
    Validate that the YAML file is a proper Ansible playbook.

    Args:
        playbook_path (str): Path to the playbook file

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with open(playbook_path, "r") as f:
            playbook_data = yaml.safe_load(f)

        # Basic validation: should be a list of plays
        if not isinstance(playbook_data, list):
            logger.error(
                f"Invalid playbook format: {playbook_path}. Should be a list of plays."
            )
            return False

        # Each item should have at least some basic play attributes
        for i, play in enumerate(playbook_data):
            if not isinstance(play, dict):
                logger.error(f"Invalid play format at index {i} in {playbook_path}")
                return False

            # Check for hosts or target attribute
            if "hosts" not in play and "targets" not in play:
                logger.warning(
                    f"Play at index {i} missing 'hosts' attribute in {playbook_path}"
                )

        return True
    except Exception as e:
        logger.error(f"Error validating playbook {playbook_path}: {str(e)}")
        return False


def format_ansible_result(result: Dict[str, Any]) -> str:
    """
    Format the Ansible result for display.

    Args:
        result (Dict[str, Any]): The Ansible result dictionary

    Returns:
        str: Formatted result string
    """
    output = []

    # Add status information
    status = result.get("status", "unknown")
    success = result.get("success", False)

    if success:
        output.append(
            f"✅ Playbook execution completed successfully with status: {status}"
        )
    else:
        output.append(f"❌ Playbook execution failed with status: {status}")

    output.append(f"Return code: {result.get('rc', -1)}")

    # Add stats information
    stats = result.get("stats", {})
    if stats:
        output.append("\nHost Stats:")
        for host, host_stats in stats.items():
            output.append(f"  {host}:")
            for stat_name, stat_value in host_stats.items():
                output.append(f"    {stat_name}: {stat_value}")

    # Join all lines with newlines
    return "\n".join(output)
