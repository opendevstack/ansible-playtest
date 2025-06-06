"""
Unit tests for the ansible_runner_api module.
This module contains pytest tests for the `run_playbook` function in the
`ansible_playbook_runner.ansible_runner_api` module. It tests various
scenarios including successful and failed playbook executions, handling of
import errors, and passing options to the ansible-runner library.

"""
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from ansible_playbook_runner.ansible_runner_api import run_playbook


class TestAnsibleRunnerAPI:
    @pytest.fixture
    def example_playbook(self):
        """Fixture to create a temporary playbook file."""
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            f.write(b"""---
- name: Test Playbook
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: Echo something
      debug:
        msg: Hello world
""")
        playbook_path = f.name
        yield playbook_path
        # Cleanup
        os.unlink(playbook_path)

    @pytest.fixture
    def mock_ansible_runner(self):
        """Mock the ansible_runner module."""
        with patch.dict('sys.modules', {'ansible_runner': MagicMock()}) as mock_runner:
            yield mock_runner

    def test_run_playbook_import_error(self, example_playbook):
        """Test handling of import errors."""
        with patch.dict('sys.modules', {'ansible_runner': None}):
            with pytest.raises(ImportError):
                # Need to import inside the test to trigger the import error
                from ansible_playbook_runner.ansible_runner_api import run_playbook
                run_playbook(example_playbook)

    def test_run_playbook_success(self, mock_ansible_runner, example_playbook):
        """Test successful playbook execution."""
        # Setup the mock
        mock_result = MagicMock()
        mock_result.status = "successful"
        mock_result.rc = 0
        mock_result.stats = {"localhost": {"ok": 1}}
        sys.modules['ansible_runner'].run.return_value = mock_result

        result = run_playbook(example_playbook)
        
        # Assertions
        assert result['status'] == 'successful'
        assert result['success'] is True
        assert result['rc'] == 0
        assert 'stats' in result
        sys.modules['ansible_runner'].run.assert_called_once()

    def test_run_playbook_failure(self, mock_ansible_runner, example_playbook):
        """Test failed playbook execution."""
        # Setup the mock
        mock_result = MagicMock()
        mock_result.status = "failed"
        mock_result.rc = 1
        mock_result.stats = {"localhost": {"failed": 1}}
        sys.modules['ansible_runner'].run.return_value = mock_result

        # Import and run
        result = run_playbook(example_playbook)
        
        # Assertions
        assert result['status'] == 'failed'
        assert result['success'] is False
        assert result['rc'] == 1
        assert 'stats' in result

    def test_run_playbook_with_options(self, mock_ansible_runner, example_playbook):
        """Test playbook execution with various options."""
        # Setup the mock
        mock_result = MagicMock()
        mock_result.status = "successful"
        mock_result.rc = 0
        mock_result.stats = {"localhost": {"ok": 1}}
        sys.modules['ansible_runner'].run.return_value = mock_result


        inventory = "/tmp/inventory.ini"
        extra_vars = {"var1": "value1"}
        private_data_dir = "/tmp/private"
        tags = ["tag1", "tag2"]
        skip_tags = ["skip1"]
        
        result = run_playbook(
            example_playbook,
            inventory_path=inventory,
            extra_vars=extra_vars,
            private_data_dir=private_data_dir,
            tags=tags,
            skip_tags=skip_tags,
            verbosity=2
        )
        
        # Assertions
        sys.modules['ansible_runner'].run.assert_called_once()
        # Get the call arguments
        call_args = sys.modules['ansible_runner'].run.call_args[1]
        assert call_args["playbook"] == example_playbook
        assert call_args["inventory"] == inventory
        assert call_args["extravars"] == extra_vars
        assert call_args["private_data_dir"] == private_data_dir
        assert call_args["tags"] == tags
        assert call_args["skip_tags"] == skip_tags
        assert call_args["verbosity"] == 2