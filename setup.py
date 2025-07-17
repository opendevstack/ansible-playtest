"""
Backward-compatible setup.py for ansible-playtest package.
The main configuration is now in pyproject.toml.
"""

from setuptools import setup

# This setup.py exists for backward compatibility with older tools
# that don't support pyproject.toml. All config is in pyproject.toml.
setup()
