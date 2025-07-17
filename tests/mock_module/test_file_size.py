import os
import pytest
import ansible_runner


@pytest.mark.modules_to_mock(
    {"community.general.filesize": "tests/mocks/community.general.filesize.py"}
)
def test_file_size_module(module_mocker):
    """Test that the file_size module is properly mocked."""
    playbook_path = os.path.join(os.path.dirname(__file__), "test_file_size.yml")

    # Run the playbook with the mocked module
    result = ansible_runner.run(
        playbook=playbook_path, host_pattern="localhost", quiet=False, verbosity=1
    )

    # Verify the playbook ran successfully
    assert result.status == "successful"

    # Find the task result for "Display file size"
    file_size_output = None
    for event in result.events:
        if (
            event.get("event") == "runner_on_ok"
            and event.get("event_data", {}).get("task") == "Display file size"
        ):
            file_size_output = event.get("event_data", {}).get("res", {}).get("msg")
            break

    # Verify our mock was used (should see 1024 bytes)
    assert file_size_output == "File size is 1024 bytes"
