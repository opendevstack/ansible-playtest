
"""
This module defines an Ansible callback plugin, `mock_module_tracker`, designed for tracking module executions during Ansible playbooks
It captures detailed information about each module call, including parameters, results, task names, and timestamps, and logs this data to a summary file. 
The plugin also tracks failed and skipped modules, along with any errors encountered, providing a comprehensive overview of playbook execution for
validation and debugging purposes.
"""

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import os
import json
import time
import datetime
from ansible.plugins.callback import CallbackBase
from ansible.utils.display import Display


DOCUMENTATION = """
    callback: mock_module_tracker
    type: notification
    short_description: Tracks module executions for testing
    version_added: "1.0"
    description:
        - This callback tracks module executions.
        - Captures call details for parameter validation and sequence verification.
    requirements:
        - Enabled in ansible.cfg
    options:
      log_file:
        description: Path to a file where module execution data will be logged
        required: False
        type: str
        default: '/tmp/ansible_mock_module_calls.log'
"""





# Create a display instance for our own use (don't rely on the one passed in __init__)
callback_display = Display()


class CallbackModule(CallbackBase):
    """
    Ansible callback plugin for tracking module executions.
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "notification"
    CALLBACK_NAME = "mock_module_tracker"
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self, display=None):
        super(CallbackModule, self).__init__(display)
        self.module_calls = {}
        self.call_details = {}  # Store detailed information about each call
        self.call_sequence = []  # Track the sequence of module calls
        self.failed_modules = {}
        self.skipped_modules = {}
        self.errors = []  # Track detailed errors for verification
        self.start_time = time.time()

        # Use our own display instance, not the one passed to __init__
        self._display.display("Mock Module Tracker callback initialized", color="green")

        # Store the current working directory (where the playbook is executed from)
        self.cwd = os.getcwd()

    #    debugpy.listen(("localhost", 5678))
    #    print("Waiting for debugger attach...")
    #    debugpy.wait_for_client()
    #    debugpy.breakpoint()

    def _increment_module_count(self, module_name):
        """Increment the count for a module"""
        if module_name not in self.module_calls:
            self.module_calls[module_name] = 0
        self.module_calls[module_name] += 1
        return self.module_calls[module_name]

    def _track_module_call(self, module_name, result):
        """
        Track detailed information about a module call

        Args:
            module_name: The name of the module called
            result: The task result object
        """
        # Add the module to the call sequence
        self.call_sequence.append(module_name)

        # Extract parameters from the task
        params = {}
        if hasattr(result, "_task") and hasattr(result._task, "args"):
            params = result._task.args

        # Extract result data if available
        result_data = {}
        if hasattr(result, "_result"):
            result_data = result._result

        # Initialize call_details for this module if it doesn't exist
        if module_name not in self.call_details:
            self.call_details[module_name] = []

        # Add the call details
        call_info = {
            "params": params,
            "result": result_data,
            "task": (
                result.task_name
                if hasattr(result, "task_name")
                else "unnamed_task"
            ),
            "timestamp": datetime.datetime.now().isoformat(),
        }

        self.call_details[module_name].append(call_info)

    def _save_summary_to_cwd(self, stats):
        """Save a summary file in the mock configuration directory or current working directory"""
        try:
            summary_filename = "playbook_statistics.json"

            # Try to get the project directory from environment variable
            project_dir = os.environ.get("ANSIBLE_TEST_TMP_DIR")
            if project_dir and os.path.isdir(project_dir):
                summary_path = os.path.join(project_dir, summary_filename)
                save_location = f"project directory ({project_dir})"
            else:
                summary_path = os.path.join(self.cwd, summary_filename)
                save_location = "current working directory"

            # Build summary data
            # Try to get playbook name from the running playbook if possible
            playbook_name = "playbook"
            if hasattr(self, "_playbook_name") and self._playbook_name:
                playbook_name = (
                    os.path.basename(self._playbook_name)
                    .replace(".yml", "")
                    .replace(".yaml", "")
                )

            # Process play recap stats for each host
            hosts_stats = {}
            for host in stats.processed.keys():
                # Use the summarize method to get host stats
                host_summary = stats.summarize(host)
                hosts_stats[host] = host_summary

            # Calculate overall stats
            total_ok = sum(host_stats["ok"] for host_stats in hosts_stats.values())
            total_changed = sum(
                host_stats["changed"] for host_stats in hosts_stats.values()
            )
            total_unreachable = sum(
                host_stats["unreachable"] for host_stats in hosts_stats.values()
            )
            total_failed = sum(
                host_stats["failures"] for host_stats in hosts_stats.values()
            )
            total_skipped = sum(
                host_stats["skipped"] for host_stats in hosts_stats.values()
            )
            total_rescued = sum(
                host_stats["rescued"] for host_stats in hosts_stats.values()
            )
            total_ignored = sum(
                host_stats["ignored"] for host_stats in hosts_stats.values()
            )

            duration = time.time() - self.start_time
            summary_data = {
                "playbook_name": playbook_name,
                "timestamp": time.ctime(),
                "duration_seconds": round(duration, 2),
                "total_module_calls": sum(self.module_calls.values()),
                "module_calls": self.module_calls,
                "call_details": self.call_details,  # Add detailed call information
                "call_sequence": self.call_sequence,  # Add call sequence
                "failed_modules": self.failed_modules,
                "total_failures": (
                    sum(self.failed_modules.values()) if self.failed_modules else 0
                ),
                "skipped_modules": self.skipped_modules,
                "total_skipped": (
                    sum(self.skipped_modules.values()) if self.skipped_modules else 0
                ),
                "errors": self.errors,  # Add detailed error information for verification
                "play_recap": {
                    "hosts": hosts_stats,
                    "totals": {
                        "ok": total_ok,
                        "changed": total_changed,
                        "unreachable": total_unreachable,
                        "failed": total_failed,
                        "skipped": total_skipped,
                        "rescued": total_rescued,
                        "ignored": total_ignored,
                    },
                },
            }

            # Write summary to file
            with open(summary_path, "w") as f:
                json.dump(summary_data, f, indent=2)

            self._display.display(
                f"Module calls summary saved to {save_location}: {summary_path}",
                color="green",
            )
            return summary_path

        except Exception as e:
            error_msg = f"Error saving summary file: {str(e)}"
            self._display.display(error_msg, color="red")
            return None

    def v2_runner_on_failed(self, result, ignore_errors=False):
        """Log module failure"""
        module_name = result._task.action
        self._increment_module_count(module_name)
        self._track_module_call(module_name, result)

        # Track failed modules
        if module_name not in self.failed_modules:
            self.failed_modules[module_name] = 0
        self.failed_modules[module_name] += 1

        # Get error message if available
        error_msg = ""

        if hasattr(result, "result") and "msg" in result.result:
            error_msg = result.result["msg"]

        # Supporting future deprecated result._result
        if hasattr(result, "_result") and "msg" in result._result:
            error_msg = result._result["msg"]


        # Add to detailed errors list for verification
        error_detail = {
            "module": module_name,
            "task": (
                result.task_name
                if hasattr(result, "task_name")
                else "unnamed_task"
            ),
            "message": error_msg,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.errors.append(error_detail)

        self._display.display(
            f"Module failure: {module_name} - {error_msg}", color="red"
        )

    def v2_runner_on_ok(self, result):
        """Log successful module execution"""
        module_name = result._task.action
        count = self._increment_module_count(module_name)
        self._track_module_call(module_name, result)

    def v2_runner_on_skipped(self, result):
        """Log skipped module execution"""
        module_name = result._task.action

        # Track skipped modules
        if module_name not in self.skipped_modules:
            self.skipped_modules[module_name] = 0
        self.skipped_modules[module_name] += 1

        # Also track this in the call sequence, but mark it as skipped
        self.call_sequence.append(f"{module_name}(skipped)")

    def v2_playbook_on_stats(self, stats):
        """Log summary at the end of playbook execution"""

        # Save the summary in the current working directory
        summary_path = self._save_summary_to_cwd(stats)
        if summary_path:
            self._display.display(f"Summary saved to: {summary_path}", color="green")

    def v2_playbook_on_start(self, playbook):
        """Capture the playbook name when it starts"""
        if hasattr(playbook, "_file_name"):
            self._playbook_name = playbook._file_name
        else:
            self._playbook_name = None
