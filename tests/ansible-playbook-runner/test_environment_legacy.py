import os
import tempfile
import shutil
import pytest
from ansible_playbook_runner import environment

class TestLegacyFunctions:
    @pytest.fixture
    def temp_dir(self):
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

    def test_create_virtual_environment_default(self, temp_dir):
        venv_path = environment.create_virtual_environment(temp_dir)
        assert os.path.exists(venv_path)
        assert os.path.exists(os.path.join(venv_path, 'bin', 'python'))
        assert os.path.exists(os.path.join(venv_path, 'bin', 'pip'))

    def test_create_virtual_environment_with_playtest(self, temp_dir, monkeypatch):
        # Patch install_ansible_playtest to avoid actual install
        class DummyVenv(environment.VirtualEnvironment):
            def install_ansible_playtest(self, src_dir=None):
                self._playtest_installed = True
        monkeypatch.setattr(environment, 'VirtualEnvironment', DummyVenv)
        venv_path = environment.create_virtual_environment(temp_dir, install_playtest=True)
        assert os.path.exists(venv_path)

    def test_install_packages(self, temp_dir, monkeypatch):
        installed = {}
        class DummyVenv(environment.VirtualEnvironment):
            def install_packages(self, packages):
                installed['pkgs'] = packages
        monkeypatch.setattr(environment, 'VirtualEnvironment', DummyVenv)
        venv_path = environment.create_virtual_environment(temp_dir)
        environment.install_packages(venv_path, ['pytest', 'requests'])
        assert installed['pkgs'] == ['pytest', 'requests']

    def test_install_packages_invalid_path(self):
        # Should not raise, just create venv in non-existent dir
        temp_dir = tempfile.mkdtemp()
        venv_path = os.path.join(temp_dir, 'venv')
        try:
            environment.install_packages(venv_path, [])
        finally:
            shutil.rmtree(temp_dir)
