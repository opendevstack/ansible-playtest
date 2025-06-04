#!/usr/bin/env python3

"""
Command-line interface for ansible-playtest:
A tool for scenario-based testing of Ansible playbooks
"""

import os
import sys
import argparse
import threading
import time

from ansible_playtest.core.playbook_runner import PlaybookRunner
from ansible_playtest.core.ansible_test_scenario import AnsibleTestScenario
from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer


def main():
    """Main function for the ansible-playtest CLI"""
    parser = argparse.ArgumentParser(
        description="Run Ansible playbooks with scenario-based testing"
    )
    parser.add_argument("playbook", help="Path to the playbook to test")
    parser.add_argument(
        "--scenario", "-s", required=True, help="Name of the scenario to use"
    )
    parser.add_argument("--inventory", "-i", help="Path to inventory file")
    parser.add_argument(
        "--extra-var", "-e", action="append", help="Extra variables (key=value format)"
    )
    parser.add_argument(
        "--keep-mocks",
        "-k",
        action="store_true",
        help="Keep mock files after execution for debugging",
    )
    parser.add_argument(
        "--config-dir",
        "-c",
        help="Directory containing scenarios and test data (overrides ANSIBLE_PLAYTEST_CONFIG_DIR environment variable)",
    )

    # SMTP server options
    smtp_group = parser.add_argument_group("SMTP Server Options")
    smtp_group.add_argument(
        "--smtp-port",
        type=int,
        default=1025,
        help="Port for the mock SMTP server (default: 1025)",
    )
    smtp_group.add_argument(
        "--start-smtp-mock",
        action="store_true",
        help="Start the mock SMTP server before running the playbook",
    )

    args = parser.parse_args()

    # Process extra vars
    extra_vars = {}
    if args.extra_var:
        for var in args.extra_var:
            if "=" in var:
                key, value = var.split("=", 1)
                extra_vars[key] = value

    # Set the config directory if specified
    if args.config_dir:
        AnsibleTestScenario.set_config_dir(args.config_dir)

    smtp_server = None
    smtp_thread = None
    try:
        if args.start_smtp_mock:
            print(f"Starting mock SMTP server on port {args.smtp_port}...")
            smtp_server = MockSMTPServer(port=args.smtp_port)
            smtp_thread = threading.Thread(target=smtp_server.start, daemon=True)
            smtp_thread.start()
            time.sleep(1)  # Give the server a moment to start
            print(f"Mock SMTP server started on port {args.smtp_port}")

        # Check playbook path
        if not os.path.exists(args.playbook):
            print(f"Error: Playbook not found at '{args.playbook}'\n")
            print("Usage example:")
            print(
                "  ansible-playtest --scenario examples/scenarios/example_scenario.yaml ./examples/playbooks/demo_playbook_01.yml"
            )
            print("\nSee INSTALL.md for more details.")
            sys.exit(2)

        # Enhanced scenario path resolution
        scenario_path = args.scenario
        scenario_found = False
        scenario_search_paths = []
        fuzzy_matches = []

        if os.path.isabs(scenario_path):
            if os.path.exists(scenario_path):
                scenario_found = True
            else:
                scenario_search_paths.append(scenario_path)
        else:
            search_dirs = []
            # a) config_dir
            if args.config_dir:
                search_dirs.append(args.config_dir)
            # b) current_dir
            search_dirs.append(os.getcwd())
            # c) all folders under current_dir/test/
            test_dir = os.path.join(os.getcwd(), "tests")
            if os.path.isdir(test_dir):
                for root, dirs, files in os.walk(test_dir):
                    search_dirs.append(root)
            # d) all folders under current_dir/test_data/
            test_data_dir = os.path.join(os.getcwd(), "test_data")
            if os.path.isdir(test_data_dir):
                for root, dirs, files in os.walk(test_data_dir):
                    search_dirs.append(root)

            # Process scenario name without extension
            scenario_name = scenario_path
            if scenario_name.endswith(".yaml") or scenario_name.endswith(".yml"):
                scenario_name = os.path.splitext(scenario_name)[0]

            scenario_candidates = []
            if not (scenario_path.endswith(".yaml") or scenario_path.endswith(".yml")):
                scenario_candidates.append(scenario_path + ".yaml")
                scenario_candidates.append(scenario_path + ".yml")
            scenario_candidates.append(scenario_path)

            # First try exact matches
            for d in search_dirs:
                for candidate in scenario_candidates:
                    candidate_path = os.path.join(d, candidate)
                    if os.path.exists(candidate_path):
                        scenario_path = candidate_path
                        scenario_found = True
                        break
                if scenario_found:
                    break
                for candidate in scenario_candidates:
                    scenario_search_paths.append(os.path.join(d, candidate))

            # If exact match not found, try fuzzy matches by searching for files that include the scenario_name
            if not scenario_found:
                # Use a set to avoid duplicate matches
                unique_matches = set()
                # Collect all possible scenario files
                for d in search_dirs:
                    if os.path.exists(d):
                        for root, _, files in os.walk(d):
                            for file in files:
                                if file.endswith(".yaml") or file.endswith(".yml"):
                                    if scenario_name.lower() in file.lower():
                                        unique_matches.add(
                                            os.path.normpath(os.path.join(root, file))
                                        )

                # Convert to list for further processing
                fuzzy_matches = list(unique_matches)

                # If exactly one fuzzy match found, use it
                if len(fuzzy_matches) == 1:
                    scenario_path = fuzzy_matches[0]
                    scenario_found = True
                    print(f"Found scenario match: {os.path.basename(scenario_path)}")
                # If multiple fuzzy matches found with different basenames, fail with a helpful error
                elif len(fuzzy_matches) > 1:
                    # Check if they all have the same basename (then pick one)
                    basenames = {os.path.basename(path) for path in fuzzy_matches}
                    if len(basenames) == 1:
                        # All matches have the same filename, just pick the first one
                        scenario_path = fuzzy_matches[0]
                        scenario_found = True
                        print(
                            f"Found multiple copies of the same scenario file. Using: {scenario_path}"
                        )
                    else:
                        print(
                            f"Error: Multiple different scenarios found matching '{scenario_name}':"
                        )
                        for match in fuzzy_matches:
                            print(f"  {match}")
                        print("\nPlease provide a more specific scenario name.")
                        sys.exit(2)

        if not scenario_found:
            print(f"Error: Scenario file not found for '{args.scenario}'\n")
            print("Searched in:")
            for p in scenario_search_paths:
                print(f"  {p}")
            # Try to list available scenarios
            config_dir = os.environ.get("ANSIBLE_PLAYTEST_CONFIG_DIR")
            if args.config_dir:
                config_dir = args.config_dir
            if not config_dir:
                config_dir = os.path.join(
                    os.path.dirname(os.path.dirname(__file__)),
                    "tests",
                    "test_data",
                    "scenarios",
                )
            print(f"Looking for scenarios in: {config_dir}")
            if os.path.isdir(config_dir):
                scenario_files = [
                    f
                    for f in os.listdir(config_dir)
                    if f.endswith(".yaml") or f.endswith(".yml")
                ]
                if scenario_files:
                    print("Available scenarios:")
                    for fname in scenario_files:
                        print(f"  {os.path.join(config_dir, fname)}")
                else:
                    print("No scenario files found in the configured directory.")
            else:
                print("Scenario directory does not exist.")
            print("\nUsage example:")
            print(
                "  ansible-playtest --scenario <scenario_path> ./examples/playbooks/demo_playbook_01.yml"
            )
            print("\nSee INSTALL.md for more details.")
            sys.exit(2)

        # Create runner instance
        runner = PlaybookRunner()
        # Run the playbook with the resolved scenario path
        success, result = runner.run_playbook_with_scenario(
            args.playbook,
            scenario_path,  # Use the resolved scenario path instead of args.scenario
            inventory_path=args.inventory,
            extra_vars=extra_vars,
            keep_mocks=args.keep_mocks,
        )
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nExecution interrupted by user.")
        sys.exit(130)
    finally:
        if smtp_server and smtp_server.is_running():
            print("Stopping mock SMTP server...")
            smtp_server.stop()
            print("Mock SMTP server stopped.")


if __name__ == "__main__":
    main()
