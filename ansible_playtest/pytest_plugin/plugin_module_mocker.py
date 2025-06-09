import pytest
from ansible_playtest.mocks.module_mocker import ModuleMocker


@pytest.fixture
def module_mocker(request):
    """
    Fixture to mock Ansible modules during test execution.
    
    Configure by setting the 'modules_to_mock' marker on the test function.
    Example:
    
    @pytest.mark.modules_to_mock({
        "community.general.file_size": "/path/to/mock/file_size.py"
    })
    def test_with_mocked_modules(module_mocker):
        # Test code that uses the mocked modules
        pass
    """
    marker = request.node.get_closest_marker("modules_to_mock")
    modules_to_mock = {}
    
    if marker:
        modules_to_mock = marker.args[0] if marker.args else {}
    
    with ModuleMocker(modules_to_mock) as mocker:
        yield mocker


def pytest_configure(config):
    """Add the 'modules_to_mock' marker to pytest."""
    config.addinivalue_line(
        "markers", 
        "modules_to_mock(dict): dictionary of Ansible modules to mock: {module_name: mock_path}"
    )