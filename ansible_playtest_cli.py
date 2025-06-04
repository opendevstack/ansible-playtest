#!/usr/bin/env python3

"""
Command-line interface for ansible-playtest:
A tool for scenario-based testing of Ansible playbooks
"""

import os
import sys
import argparse

from ansible_playtest.core.playbook_runner import (
    PlaybookRunner
)

# Add the src directory to path to make imports work
script_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(script_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)



def main():
    """Main function for the ansible-playtest CLI"""
    parser = argparse.ArgumentParser(description='Run Ansible playbooks with scenario-based testing')
    parser.add_argument('playbook', help='Path to the playbook to test')
    parser.add_argument('--scenario', '-s', required=True, help='Name of the scenario to use')
    parser.add_argument('--inventory', '-i', help='Path to inventory file')
    parser.add_argument('--extra-var', '-e', action='append', help='Extra variables (key=value format)')
    parser.add_argument('--keep-mocks', '-k', action='store_true', help='Keep mock files after execution for debugging')

    # SMTP server options
    smtp_group = parser.add_argument_group('SMTP Server Options')
    smtp_group.add_argument('--no-smtp', action='store_true', help='Disable mock SMTP server')
    smtp_group.add_argument('--smtp-port', type=int, default=1025, help='Port for the mock SMTP server (default: 1025)')
    
    args = parser.parse_args()
    
    # Process extra vars
    extra_vars = {}
    if args.extra_var:
        for var in args.extra_var:
            if '=' in var:
                key, value = var.split('=', 1)
                extra_vars[key] = value
    
    # Run the playbook with the specified scenario using the class
    runner = PlaybookRunner()
    success, _ = runner.run_playbook_with_scenario(
        args.playbook,
        args.scenario,
        inventory_path=args.inventory,
        extra_vars=extra_vars,
        keep_mocks=args.keep_mocks,
    )
    
    # Exit with appropriate return code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
