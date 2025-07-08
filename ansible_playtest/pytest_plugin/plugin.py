"""
Pytest fixtures and configuration for AnsiblePlayTest
"""

from __future__ import annotations
import os
import sys
import pytest
import ansible_playtest.ansible_callback
from ansible_playtest.core.playbook_runner import PlaybookRunner
from ansible_playtest.core.scenario_factory import ScenarioFactory
from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


@pytest.fixture(scope="session", autouse=True)
def setup_ansible_environment(request):
    """
    Set up the environment variables for Ansible tests.
    This ensures that our mock module tracker callback is correctly loaded.
    """
    # Store original environment
    original_env = os.environ.copy()

    # Set up the environment for all tests
    # Use a helper function to determine the ansible.cfg path
    ansible_cfg_path = _get_ansible_cfg_path(request)
    if ansible_cfg_path is not None:
        os.environ["ANSIBLE_CONFIG"] = ansible_cfg_path
        print(f"[PLUGIN] Using ansible.cfg at {ansible_cfg_path}")

    # Find the absolute path to the ansible_callback directory that contains mock_module_tracker.py
    # This will work whether the package is installed or in development mode

    # Get the directory containing the ansible_callback package
    callback_dir = os.path.dirname(ansible_playtest.ansible_callback.__file__)

    os.environ["ANSIBLE_CALLBACK_PLUGINS"] = callback_dir

    os.environ["ANSIBLE_CALLBACKS_ENABLED"] = "mock_module_tracker"

    # Set up custom collections path if specified
    collections_dir = request.config.getoption("--ansible-playtest-collections-dir")
    if collections_dir:
        os.environ["ANSIBLE_PLAYTEST_COLLECTIONS_DIR"] = collections_dir

    # Set up custom mock collections path if specified
    collections_mock_dir = request.config.getoption(
        "--ansible-playtest-mock-collections-dir"
    )
    if collections_mock_dir:
        os.environ["ANSIBLE_PLAYTEST_MOCK_COLLECTIONS_DIR"] = collections_mock_dir

    # Set up custom mocked collections path if specified
    mocked_collections = request.config.getoption(
        "--ansible-playtest-mocked-collections"
    )
    if mocked_collections:
        os.environ["ANSIBLE_COLLECTIONS_PATH"] = mocked_collections

    # Let the test run
    yield

    # Restore the original environment when done
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def smtp_mock_server(request):
    """Get SMTP mock configuration from marker and start SMTP mock server"""
    marker = request.node.get_closest_marker("smtp_mock_server")
    port = 1025  # Default SMTP port

    if marker and marker.kwargs.get("port"):
        port = marker.kwargs["port"]
    print(f"[PLUGIN] Starting mock SMTP server on port {port}")

    # Create and start the mock SMTP server
    server = MockSMTPServer(port=port, verbose=0)
    server.start()

    # Yield the server instance so tests can use it
    yield server

    # Stop the server when the test is complete
    print(f"[PLUGIN] Stopping mock SMTP server on port {port}")
    server.stop()


@pytest.fixture
def mock_modules(request):
    """Get mock modules from marker or return None"""
    marker = request.node.get_closest_marker("mock_modules")
    return marker.args[0] if marker else None


@pytest.fixture
def playbook_runner(request):
    playbook_path = None
    scenario_path = None
    inventory_path = None
    extra_vars = None
    keep_artifacts = False
    use_virtualenv = False
    requirements = None
    verbosity = 1


    if hasattr(request, "param"):
        playbook_path = request.param.get("playbook_path")
        scenario_path = request.param.get("scenario_path")
    else:
        # For direct access, get from function args
        func_args = request.node.funcargs
        playbook_path = func_args.get("playbook_path")
        scenario_path = func_args.get("scenario_path")

    inventory_path = _get_inventory_path(request)

    extra_vars = getattr(request.node, "extra_vars", None)

    keep_artifacts = _get_keep_artifacts(request)

    use_virtualenv = _get_use_virtualenv(request)

    # Get requirements options
    requirements = None
    if use_virtualenv:
        requirements = _get_requirements(request)

    # Get mock_collections_dir
    mock_collections_directory = _get_mock_collections_dir(request)
    
    # Get verbosity level
    verbosity = _get_verbosity(request)
    
    # Check if module_mocker fixture is available
    module_mocker = None
    if hasattr(request, 'node') and hasattr(request.node, 'funcargs'):
        module_mocker = request.node.funcargs.get('module_mocker')

    # Create a new PlaybookRunner instance
    runner = PlaybookRunner(
        scenario=scenario_path,
        use_virtualenv=use_virtualenv,
        requirements=requirements,
        mock_collections_dir=mock_collections_directory,
        module_mocker=module_mocker,
    )

    # Set up virtualenv if needed before running the playbook
    if use_virtualenv:
        print("\nSetting up virtual environment for playbook execution...")
        if not runner.setup_virtualenv():
            pytest.fail("Failed to set up virtual environment for playbook execution")
        print("Virtual environment ready.")

    runner.run_playbook_with_scenario(
        playbook_path=playbook_path,
        scenario_name=scenario_path,
        inventory_path=inventory_path,
        extra_vars=extra_vars,
        keep_mocks=keep_artifacts,
        verbosity=verbosity
    )

    # Yield the runner to the test function
    yield runner

    if not keep_artifacts:
        runner.cleanup()


def pytest_generate_tests(metafunc):
    """
    Auto-discover and generate tests for all scenarios and playbooks.
    """
    if (
        "scenario_path" in metafunc.fixturenames
        and "playbook_path" in metafunc.fixturenames
    ):
        # Get scenarios and playbooks directory from markers or command line options
        scenarios_dir = _get_scenarios_dir(metafunc)
        playbooks_dir = _get_playbooks_dir(metafunc)

        # Use ScenarioFactory to discover scenarios
        factory = ScenarioFactory(
            config_dir=os.path.dirname(scenarios_dir),
            scenarios_dir=scenarios_dir,
            playbooks_dir=playbooks_dir,
        )
        discovered = factory.discover_scenarios()

        test_params = []
        test_ids = []
        for scenario_path, playbook_path, scenario_id in discovered:
            test_params.append((playbook_path, scenario_path))
            test_ids.append(scenario_id)

        metafunc.parametrize("playbook_path,scenario_path", test_params, ids=test_ids)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add Ansible scenario test options to pytest"""
    group = parser.getgroup("ansible-playtest", "Ansible Playbook Testing")

    group.addoption(
        "--ansible-playtest-keep-artifacts",
        action="store_true",
        default=False,
        help="Keep test artifacts after test completion",
    )
    group.addoption(
        "--ansible-playtest-scenarios-dir",
        action="store",
        default=os.environ.get(
            "ANSIBLE_PLAYTEST_SCENARIOS_DIR", "tests/test_data/scenarios"
        ),
        help="Directory containing scenario files to test",
    )
    group.addoption(
        "--ansible-playtest-mock-collections-dir",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_MOCK_COLLECTIONS_DIR", None),
        help="Path to directory containing mock collections for testing",
    )
    group.addoption(
        "--ansible-playtest-playbook-dir",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_PLAYBOOKS_DIR", "playbooks"),
        help="Directory containing playbooks to test",
    )
    group.addoption(
        "--ansible-playtest-ansible-cfg",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_ANSIBLE_CFG", None),
        help="Path to ansible.cfg file to use for tests",
    )
    group.addoption(
        "--ansible-playtest-inventory",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_INVENTORY", None),
        help="Path to inventory file or directory to use for tests",
    )
    group.addoption(
        "--ansible-playtest-mocked-collections",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_MOCKED_COLLECTIONS", None),
        help="Path to directory with mocked Ansible collections",
    )
    group.addoption(
        "--ansible-playtest-collections-dir",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_COLLECTIONS_DIR", None),
        help="Path to the ansible_collections directory to use for tests",
    )
    group.addoption(
        "--skip-auto-discovery",
        action="store_true",
        default=False,
        help="Skip auto-discovery of scenario files",
    )

    # Add virtualenv-related options
    group.addoption(
        "--ansible-playtest-use-virtualenv",
        action="store_true",
        default=os.environ.get("ANSIBLE_PLAYTEST_USE_VIRTUALENV", "false").lower()
        == "true",
        help="Run playbooks in a fresh virtual environment",
    )
    group.addoption(
        "--ansible-playtest-requirements",
        action="store",
        default=os.environ.get("ANSIBLE_PLAYTEST_REQUIREMENTS", None),
        help="Path to requirements file for the virtual environment",
    )
    group.addoption(
        "--ansible-playtest-requirements-packages",
        action="append",
        default=(
            os.environ.get("ANSIBLE_PLAYTEST_REQUIREMENTS_PACKAGES", "").split(",")
            if os.environ.get("ANSIBLE_PLAYTEST_REQUIREMENTS_PACKAGES", "")
            else []
        ),
        help="Additional packages to install in the virtual environment (comma-separated)",
    )
    group.addoption(
        "--ansible-playtest-verbosity",
        action="store",
        type=int,
        default=int(os.environ.get("ANSIBLE_PLAYTEST_VERBOSITY", "1")),
        help="Verbosity level for Ansible playbook execution (1-5, default: 1)",
    )


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line(
        "markers", "mock_modules(modules): mock the specified list of Ansible modules"
    )
    config.addinivalue_line(
        "markers", "smtp_mock_server(port=1025): enable SMTP mock server"
    )
    config.addinivalue_line(
        "markers", "ansible_scenario(name): identify a test as an Ansible scenario test"
    )
    config.addinivalue_line(
        "markers", "keep_artifacts: keep test artifacts after test completion"
    )
    config.addinivalue_line(
        "markers",
        "use_virtualenv(requirements=None): run the playbook in a virtual environment",
    )
    config.addinivalue_line(
        "markers",
        "requirements_file(path): specify path to requirements file for virtual environment",
    )
    config.addinivalue_line(
        "markers",
        "mock_collections_dir(path): specify path to mock collections directory",
    )
    config.addinivalue_line(
        "markers",
        "inventory_path(path): specify path to the inventory file",
    )
    config.addinivalue_line(
        "markers",
        "scenarios_dir(path): specify path to the scenarios directory",
    )
    config.addinivalue_line(
        "markers",
        "playbooks_dir(path): specify path to the playbooks directory",
    )
    config.addinivalue_line(
        "markers",
        "verbosity(level): specify verbosity level for Ansible playbook execution (0-4)",
    )


def _get_inventory_path(request):
    """Helper function to get inventory path from marker or CLI option."""
    marker = request.node.get_closest_marker("inventory_path")
    inventory_path = None

    if marker and marker.args:
        inventory_path = marker.args[0]
    else:
        inventory_path = request.config.getoption("--ansible-playtest-inventory", None)

    if inventory_path:
        if not os.path.isabs(inventory_path):
            inventory_path = os.path.abspath(os.path.join(os.getcwd(), inventory_path))

        if not os.path.exists(inventory_path):
            print(f"Warning: Inventory path '{inventory_path}' does not exist.")
            return None  # Or raise an exception, depending on desired behavior

    return inventory_path


def _get_ansible_cfg_path(request):
    """
    Determine the path to the ansible.cfg file.
    It checks if a custom ansible.cfg is provided via marker or CLI option.
    If not, it uses the default ansible.cfg in the resources directory.
    """
    marker = request.node.get_closest_marker("ansible_cfg_path")
    ansible_cfg_path = None

    if marker and marker.args:
        ansible_cfg_path = marker.args[0]
    else:
        ansible_cfg_path = request.config.getoption(
            "--ansible-playtest-ansible-cfg", None
        )

    if ansible_cfg_path:
        if not os.path.isabs(ansible_cfg_path):
            ansible_cfg_path = os.path.abspath(
                os.path.join(os.getcwd(), ansible_cfg_path)
            )

        if not os.path.exists(ansible_cfg_path):
            print(f"Warning: Ansible config path '{ansible_cfg_path}' does not exist.")
            return None  # Or raise an exception, depending on desired behavior

        return ansible_cfg_path

    # If no custom ansible_cfg is provided, use the default one in the resources directory
    ansible_cfg_path = os.path.abspath(os.path.join(os.getcwd(), "ansible.cfg"))

    # If there is a file named ansible.cfg in current directory, use it
    if not os.path.exists("ansible.cfg"):
        return None

    return ansible_cfg_path


def _get_scenarios_dir(request_or_metafunc):
    """
    Helper function to get scenarios directory from marker or CLI option.
    Works with both request and metafunc objects.
    """
    scenarios_dir = None

    # Handle different object types (request vs metafunc)
    if hasattr(request_or_metafunc, "node"):
        # This is a request object
        marker = request_or_metafunc.node.get_closest_marker("scenarios_dir")
        if marker and marker.args:
            scenarios_dir = marker.args[0]
    else:
        if hasattr(request_or_metafunc, "definition") and hasattr(
            request_or_metafunc.definition, "own_markers"
        ):
            for mark in request_or_metafunc.definition.own_markers:
                if mark.name == "scenarios_dir" and mark.args:
                    scenarios_dir = mark.args[0]
                    break

    # If not found in markers, use CLI option
    if not scenarios_dir:
        config = request_or_metafunc.config
        scenarios_dir = config.getoption("--ansible-playtest-scenarios-dir")

    # Convert to absolute path if it's a relative path
    if scenarios_dir and not os.path.isabs(scenarios_dir):
        scenarios_dir = os.path.abspath(os.path.join(os.getcwd(), scenarios_dir))

    return scenarios_dir


def _get_playbooks_dir(request_or_metafunc):
    """
    Helper function to get playbooks directory from marker or CLI option.
    Works with both request and metafunc objects.
    """
    playbooks_dir = None

    # Handle different object types (request vs metafunc)
    if hasattr(request_or_metafunc, "node"):
        # This is a request object
        marker = request_or_metafunc.node.get_closest_marker("playbooks_dir")
        if marker and marker.args:
            playbooks_dir = marker.args[0]
    else:
        if hasattr(request_or_metafunc, "definition") and hasattr(
            request_or_metafunc.definition, "own_markers"
        ):
            for mark in request_or_metafunc.definition.own_markers:
                if mark.name == "playbooks_dir" and mark.args:
                    playbooks_dir = mark.args[0]
                    break

    # If not found in markers, use CLI option
    if not playbooks_dir:
        config = request_or_metafunc.config
        playbooks_dir = config.getoption("--ansible-playtest-playbook-dir")

    # Convert to absolute path if it's a relative path
    if playbooks_dir and not os.path.isabs(playbooks_dir):
        playbooks_dir = os.path.abspath(os.path.join(os.getcwd(), playbooks_dir))

    return playbooks_dir


def _get_keep_artifacts(request):
    """
    Determine whether to keep test artifacts based on the pytest configuration and markers.
    """
    # Check for keep_artifacts marker first, then fall back to command line option
    keep_artifacts_marker = request.node.get_closest_marker("keep_artifacts")
    keep_artifacts = keep_artifacts_marker is not None or request.config.getoption(
        "--ansible-playtest-keep-artifacts", False
    )
    return keep_artifacts


def _get_requirements(request):
    """
    Determine which requirements to use based on markers and configuration options.
    Returns a file path, list of packages, or None.
    """
    requirements = None

    # Check for requirements_file marker first
    requirements_marker = request.node.get_closest_marker("requirements_file")
    if requirements_marker and requirements_marker.args:
        return requirements_marker.args[0]

    # Next try command-line options
    requirements_file = request.config.getoption(
        "--ansible-playtest-requirements", None
    )
    requirements_packages = request.config.getoption(
        "--ansible-playtest-requirements-packages", []
    )

    if requirements_file and requirements_packages:
        print("Warning: Both requirements file and packages specified. Using file.")
        requirements = requirements_file
    elif requirements_file:
        requirements = requirements_file
    elif requirements_packages:
        requirements = requirements_packages

    # Finally, check virtualenv marker requirements parameter
    virtualenv_marker = request.node.get_closest_marker("use_virtualenv")
    if virtualenv_marker and virtualenv_marker.kwargs.get("requirements"):
        requirements = virtualenv_marker.kwargs.get("requirements")

    return requirements


def _get_mock_collections_dir(request):
    """
    Get the mock collections directory from marker, options, or environment variables.
    """
    mock_dir = None

    # First check if there's a marker on the test
    marker = request.node.get_closest_marker("mock_collections_dir")
    if marker and marker.args:
        mock_dir = marker.args[0]

    # If no marker, check request param
    if not mock_dir:
        mock_dir = getattr(request.node, "mock_collections_dir", None)

    # If no marker or request param, check command line option
    if not mock_dir:
        mock_dir = request.config.getoption(
            "--ansible-playtest-mock-collections-dir", None
        )

    # Convert to absolute path if it's a relative path
    if mock_dir and not os.path.isabs(mock_dir):
        mock_dir = os.path.abspath(os.path.join(os.getcwd(), mock_dir))

    return mock_dir


def _get_use_virtualenv(request):
    """
    Determine whether to use a virtual environment based on the pytest configuration and markers.
    """
    # Check for the command line option first
    use_virtualenv = request.config.getoption(
        "--ansible-playtest-use-virtualenv", False
    )

    # Override with the marker if it exists
    virtualenv_marker = request.node.get_closest_marker("use_virtualenv")
    if virtualenv_marker is not None:
        use_virtualenv = True

    return use_virtualenv


def _get_verbosity(request):
    """
    Get the verbosity level from markers or CLI options.
    """
    # Check for verbosity marker first
    verbosity_marker = request.node.get_closest_marker("verbosity")
    if verbosity_marker and verbosity_marker.args:
        return verbosity_marker.args[0]
    
    # Fall back to command line option
    verbosity = request.config.getoption("--ansible-playtest-verbosity", 0)
    
    return verbosity
