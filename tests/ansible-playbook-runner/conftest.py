import os
import sys
import tempfile
import shutil
import pytest
import yaml

@pytest.fixture(scope="session")
def temp_test_dir():
    """Create a temporary directory for all tests."""
    temp_dir = tempfile.mkdtemp(prefix="ansible_test_")
    yield temp_dir
    # Clean up after all tests
    shutil.rmtree(temp_dir, ignore_errors=True)

@pytest.fixture
def example_playbook():
    """Create a simple Ansible playbook file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
        content = """---
- name: Test Playbook
  hosts: localhost
  connection: local
  gather_facts: no
  tasks:
    - name: Echo something
      debug:
        msg: Hello world
"""
        f.write(content.encode())
        playbook_path = f.name
    
    yield playbook_path
    
    # Clean up
    if os.path.exists(playbook_path):
        os.unlink(playbook_path)

@pytest.fixture
def example_inventory():
    """Create a simple inventory file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".ini", delete=False) as f:
        content = """[local]
localhost ansible_connection=local
"""
        f.write(content.encode())
        inventory_path = f.name
    
    yield inventory_path
    
    # Clean up
    if os.path.exists(inventory_path):
        os.unlink(inventory_path)

@pytest.fixture
def mock_ansible_runner_module():
    """Mock the ansible_runner module for testing."""
    class MockResult:
        def __init__(self, status="successful", rc=0):
            self.status = status
            self.rc = rc
            self.stats = {"localhost": {"ok": 1}} if status == "successful" else {"localhost": {"failed": 1}}
            self.events = []
    
    class MockAnsibleRunner:
        @staticmethod
        def run(**kwargs):
            return MockResult()
    
    with pytest.MonkeyPatch.context() as mp:
        mock_module = type("MockAnsibleRunner", (), {"run": MockAnsibleRunner.run})
        mp.setitem(sys.modules, "ansible_runner", mock_module)
        yield mock_module