import os
import tempfile
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner
from ansible_playbook_runner.cli import cli

class TestCLI:
    @pytest.fixture
    def runner(self):
        """Fixture to create a CLI runner."""
        return CliRunner()
    
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

    def test_cli_help(self, runner):
        """Test that the CLI help command works."""
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'Run an Ansible playbook in a temporary virtual environment' in result.output

    def test_cli_missing_playbook(self, runner):
        """Test that the CLI fails when no playbook is provided."""
        result = runner.invoke(cli)
        assert result.exit_code != 0
        assert 'Missing argument' in result.output

    @patch('ansible_playbook_runner.ansible_runner_api.VirtualEnvironment')
    @patch('ansible_playbook_runner.utils.validate_playbook')
    @patch('ansible_playbook_runner.cli.create_temp_directory')
    @patch('subprocess.run')
    @patch('json.loads')
    def test_cli_runs_playbook(self, mock_json_loads, mock_run, mock_create_temp, 
                              mock_validate, mock_virtualenv, 
                              runner, example_playbook):
        """Test that the CLI runs a playbook with the correct arguments."""
        # Setup mocks
        mock_create_temp.return_value = "/tmp/test_dir"
        mock_validate.return_value = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"status": "successful", "rc": 0, "success": true, "stats": {"localhost": {"ok": 1, "changed": 0}}}'
        )
        mock_json_loads.return_value = {
            "status": "successful", 
            "rc": 0, 
            "success": True, 
            "stats": {"localhost": {"ok": 1, "changed": 0}}
        }

        # Mock VirtualEnvironment instance and its methods
        mock_venv_instance = MagicMock()
        mock_virtualenv.return_value = mock_venv_instance
        mock_venv_instance.create.return_value = None
        mock_venv_instance.install_packages.return_value = None
        mock_venv_instance.install_requirements.return_value = None
        mock_venv_instance.run_command.return_value = MagicMock(returncode=0, stdout='{"status": "successful", "rc": 0, "success": true, "stats": {"localhost": {"ok": 1, "changed": 0}}}', stderr='')
        
        # Run the CLI
        result = runner.invoke(cli, [example_playbook])
        
        # Checks
        assert mock_create_temp.called
        assert mock_virtualenv.called
        assert mock_venv_instance.create.called
        assert mock_validate.called_with(example_playbook)
        assert result.exit_code == 0