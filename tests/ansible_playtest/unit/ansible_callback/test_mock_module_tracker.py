"""
Unit tests for the CallbackModule class in mock_module_tracker.py
"""

from unittest.mock import MagicMock, patch, mock_open
import pytest
from ansible_playtest.ansible_callback.mock_module_tracker import CallbackModule


class TestCallbackModule:
    """Tests for the CallbackModule class in mock_module_tracker.py"""

    @pytest.fixture
    def callback_module(self):
        """Create a CallbackModule instance with mocked display"""
        with patch('ansible_playtest.ansible_callback.mock_module_tracker.Display') as mock_display:
            callback = CallbackModule()
            callback._display = MagicMock()
            return callback

    @pytest.fixture
    def mock_result(self):
        """Create a mock result object for testing"""
        result = MagicMock()
        result._task = MagicMock()
        result._task.action = "test_module"
        result._task.args = {"param1": "value1", "param2": "value2"}
        result._result = {"changed": True, "msg": "Test message"}
        result.task_name = "Test Task"
        return result

    @pytest.fixture
    def mock_stats(self):
        """Create mock stats for testing"""
        stats = MagicMock()
        stats.processed = {"localhost": {}}
        
        # Create a summarize method that returns the expected data structure
        def mock_summarize(host):
            return {
                "ok": 2,
                "changed": 1,
                "unreachable": 0,
                "failures": 0,
                "skipped": 1,
                "rescued": 0,
                "ignored": 0
            }
        
        stats.summarize = mock_summarize
        return stats
    
    def test_init(self, callback_module):
        """Test initialization of CallbackModule"""
        assert callback_module.module_calls == {}
        assert callback_module.call_details == {}
        assert callback_module.call_sequence == []
        assert callback_module.failed_modules == {}
        assert callback_module.skipped_modules == {}
        assert callback_module.errors == []
        assert hasattr(callback_module, "start_time")
        assert hasattr(callback_module, "cwd")
        assert callback_module.CALLBACK_NAME == "mock_module_tracker"
    
    def test_increment_module_count(self, callback_module):
        """Test _increment_module_count method"""
        # First call should initialize and return 1
        count = callback_module._increment_module_count("test_module")
        assert count == 1
        assert callback_module.module_calls["test_module"] == 1
        
        # Second call should increment and return 2
        count = callback_module._increment_module_count("test_module")
        assert count == 2
        assert callback_module.module_calls["test_module"] == 2
    
    def test_track_module_call(self, callback_module, mock_result):
        """Test _track_module_call method"""
        callback_module._track_module_call("test_module", mock_result)
        
        # Verify call sequence is updated
        assert callback_module.call_sequence == ["test_module"]
        
        # Verify call details are stored
        assert "test_module" in callback_module.call_details
        assert len(callback_module.call_details["test_module"]) == 1
        
        call_info = callback_module.call_details["test_module"][0]
        assert call_info["params"] == {"param1": "value1", "param2": "value2"}
        assert call_info["result"] == {"changed": True, "msg": "Test message"}
        assert call_info["task"] == "Test Task"
        assert "timestamp" in call_info
    
    def test_v2_runner_on_ok(self, callback_module, mock_result):
        """Test v2_runner_on_ok method"""
        callback_module.v2_runner_on_ok(mock_result)
        
        # Verify module count is incremented
        assert callback_module.module_calls["test_module"] == 1
        
        # Verify module call is tracked
        assert "test_module" in callback_module.call_details
        assert len(callback_module.call_sequence) == 1
    
    def test_v2_runner_on_failed(self, callback_module, mock_result):
        """Test v2_runner_on_failed method"""
        callback_module.v2_runner_on_failed(mock_result)
        
        # Verify module count is incremented
        assert callback_module.module_calls["test_module"] == 1
        
        # Verify module call is tracked
        assert "test_module" in callback_module.call_details
        
        # Verify failed module is tracked
        assert callback_module.failed_modules["test_module"] == 1
        
        # Verify error is tracked
        assert len(callback_module.errors) == 1
        error = callback_module.errors[0]
        assert error["module"] == "test_module"
        assert error["task"] == "Test Task"
        assert error["message"] == "Test message"
        assert "timestamp" in error
    
    def test_v2_runner_on_skipped(self, callback_module, mock_result):
        """Test v2_runner_on_skipped method"""
        callback_module.v2_runner_on_skipped(mock_result)
        
        # Verify skipped module is tracked
        assert callback_module.skipped_modules["test_module"] == 1
        
        # Verify call sequence is updated with skipped marker
        assert callback_module.call_sequence == ["test_module(skipped)"]
    
    def test_v2_playbook_on_start(self, callback_module):
        """Test v2_playbook_on_start method"""
        # Test with playbook with _file_name
        playbook = MagicMock()
        playbook._file_name = "/path/to/test_playbook.yml"
        
        callback_module.v2_playbook_on_start(playbook)
        assert callback_module._playbook_name == "/path/to/test_playbook.yml"
        
        # Test with playbook without _file_name
        playbook = MagicMock()
        playbook._file_name = None
        
        callback_module.v2_playbook_on_start(playbook)
        assert callback_module._playbook_name is None
    
    @patch('os.environ.get')
    @patch('os.path.isdir')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_summary_to_cwd_env_var(self, mock_open_file, mock_json_dump, 
                                          mock_isdir, mock_env_get, callback_module, mock_stats):
        """Test _save_summary_to_cwd with environment variable"""
        # Setup environment variable test
        mock_env_get.return_value = "/tmp/test_dir"
        mock_isdir.return_value = True
        callback_module._playbook_name = "/path/to/test_playbook.yml"
        
        # Run the method
        result = callback_module._save_summary_to_cwd(mock_stats)
        
        # Verify result
        assert result == "/tmp/test_dir/playbook_statistics.json"
        mock_open_file.assert_called_once_with("/tmp/test_dir/playbook_statistics.json", "w")
        mock_json_dump.assert_called_once()
    
    @patch('os.environ.get')
    @patch('json.dump')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_summary_to_cwd_no_env_var(self, mock_open_file, mock_json_dump, 
                                            mock_env_get, callback_module, mock_stats):
        """Test _save_summary_to_cwd without environment variable"""
        # Setup with no environment variable
        mock_env_get.return_value = None
        callback_module.cwd = "/current/work/dir"
        callback_module._playbook_name = "/path/to/test_playbook.yml"
        
        # Run the method
        result = callback_module._save_summary_to_cwd(mock_stats)
        
        # Verify result
        assert result == "/current/work/dir/playbook_statistics.json"
        mock_open_file.assert_called_once_with("/current/work/dir/playbook_statistics.json", "w")
        mock_json_dump.assert_called_once()
    
    @patch('os.environ.get')
    @patch('json.dump')
    @patch('builtins.open')
    def test_save_summary_to_cwd_exception(self, mock_open_file, mock_json_dump, 
                                           mock_env_get, callback_module, mock_stats):
        """Test _save_summary_to_cwd with exception"""
        # Setup to raise exception
        mock_env_get.return_value = None
        mock_open_file.side_effect = Exception("Test exception")
        
        # Run the method
        result = callback_module._save_summary_to_cwd(mock_stats)
        
        # Verify result
        assert result is None
        callback_module._display.display.assert_called_with(
            "Error saving summary file: Test exception", color="red")
    
    @patch.object(CallbackModule, '_save_summary_to_cwd')
    def test_v2_playbook_on_stats(self, mock_save_summary, callback_module, mock_stats):
        """Test v2_playbook_on_stats method"""
        # Setup mock to return a path
        mock_save_summary.return_value = "/path/to/summary.json"
        
        # Run the method
        callback_module.v2_playbook_on_stats(mock_stats)
        
        # Verify call to _save_summary_to_cwd
        mock_save_summary.assert_called_once_with(mock_stats)
        
        # Verify display message
        callback_module._display.display.assert_called_with(
            "Summary saved to: /path/to/summary.json", color="green")
