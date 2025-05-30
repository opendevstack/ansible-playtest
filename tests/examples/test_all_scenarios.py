"""
Example test using ansible-playtest framework to test Ansible playbooks.
This test demonstrates how to use the framework to run all scenarios.
"""
import os
import pytest

from ansible_playtest.core.test_runner import AnsiblePlaybookTestRunner
from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer

# Get this path as the base directory for examples
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))


@pytest.mark.smtp_mock(port=2026)
def test_email(smtp_mock: MockSMTPServer):
    assert smtp_mock.port == 2026


@pytest.mark.smtp_mock
@pytest.mark.ansible_playbook_test_runner(EXAMPLES_DIR)
def test_demo_all_scenarios(smtp_mock: MockSMTPServer, ansible_playbook_test_runner: AnsiblePlaybookTestRunner):
    print(smtp_mock)
    ansible_playbook_test_runner.run()
    print("Running all scenarios...")
    """
    Run all scenarios.
    """