"""
Pytest fixtures and configuration for AnsiblePlayTest
"""
from __future__ import annotations
import pytest
from ansible_playtest.core.test_runner import AnsiblePlaybookTestRunner


@pytest.fixture
def ansible_playbook_test_runner(request):
    """
    Fixture to create and return an AnsiblePlaybookTestRunner instance
    
    This fixture handles setup and teardown of the test runner.
    """
    # Get parameters from the test
    playbook_path = getattr(request.node, 'playbook_path', None)
    scenario_path = getattr(request.node, 'scenario_path', None)
    inventory_path = getattr(request.node, 'inventory_path', None)
    extra_vars = getattr(request.node, 'extra_vars', None)
    
    # Initialize test runner
    runner = AnsiblePlaybookTestRunner(
        playbook_path=playbook_path,
        scenario_path=scenario_path,
        inventory_path=inventory_path,
        extra_vars=extra_vars
    )
    
    # Give the runner to the test function
    yield runner
    
    # Clean up after test
    keep_artifacts = request.config.getoption('--keep-artifacts', False)
    if not keep_artifacts:
        runner.cleanup()

@pytest.fixture
def mock_modules(request):
    """Get mock modules from marker or return None"""
    marker = request.node.get_closest_marker("mock_modules")
    return marker.args[0] if marker else None

@pytest.fixture
def smtp_mock(request):
    """Get SMTP mock configuration from marker and start SMTP mock server"""
    from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer
    
    marker = request.node.get_closest_marker("smtp_mock")
    port = 1025  # Default SMTP port
    
    if marker and marker.kwargs.get("port"):
        port = marker.kwargs["port"]
    print(f"[PLUGIN] Starting mock SMTP server on port {port}")
    
    # Create and start the mock SMTP server
    server = MockSMTPServer(port=port,verbose=0)
    server.start()
    
    # Yield the server instance so tests can use it
    yield server
    
    # Stop the server when the test is complete
    print(f"[PLUGIN] Stopping mock SMTP server on port {port}")
    server.stop()
    

def pytest_addoption(parser: pytest.Parser) -> None:
    """Add Ansible scenario test options to pytest"""
    parser.addoption(
        "--ansible-playtest-keep-artifacts", 
        action="store_true", 
        default=False,
        help="Keep test artifacts after test completion"
    )
    parser.addoption(
        "--ansible-playtest-scenarios-dir", 
        action="store", 
        default=None,
        help="Directory containing scenario files to test"
    )
    parser.addoption(
        "--ansible-playtest-playbook-dir", 
        action="store", 
        default=None,
        help="Directory containing playbooks to test"
    )

def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "mock_modules(modules): mock the specified list of Ansible modules"
    )
    config.addinivalue_line(
        "markers", "smtp_mock(port=1025): enable SMTP mock server"
    )
    config.addinivalue_line(
        "markers", "ansible_scenario(name): identify a test as an Ansible scenario test"
    )
