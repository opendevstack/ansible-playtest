#!/usr/bin/python

# Copyright: (c) 2023, Demo Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: custom_processor
short_description: Process data in a custom way
description:
    - This module processes data according to business rules
options:
    project_id:
        description:
            - ID of the project to process
        required: true
        type: str
    action:
        description:
            - Action to perform on the project
        required: true
        choices: ['archive', 'delete', 'notify']
        type: str
    metadata:
        description:
            - Additional metadata for the process
        required: false
        type: dict
author:
    - Demo Team (@demoteam)
'''

EXAMPLES = r'''
# Archive a project
- name: Archive project
  custom_processor:
    project_id: PROJ123
    action: archive

# Delete a project with metadata
- name: Delete project
  custom_processor:
    project_id: PROJ456
    action: delete
    metadata:
      reason: expired
      confirmed_by: admin
'''

RETURN = r'''
success:
    description: Whether the operation was successful
    type: bool
    returned: always
message:
    description: Status message
    type: str
    returned: always
project_id:
    description: The processed project ID
    type: str
    returned: always
'''

from ansible.module_utils.basic import AnsibleModule


def run_module():
    # Define available arguments/parameters
    module_args = dict(
        project_id=dict(type='str', required=True),
        action=dict(type='str', required=True, choices=['archive', 'delete', 'notify']),
        metadata=dict(type='dict', required=False, default={})
    )

    # Seed the result dict
    result = dict(
        changed=False,
        success=False,
        message='',
        project_id=''
    )

    # Support check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    # If in check mode, return without making changes
    if module.check_mode:
        result['message'] = 'Check mode: would process project'
        result['project_id'] = module.params['project_id']
        module.exit_json(**result)

    # Process according to action
    action = module.params['action']
    project_id = module.params['project_id']
    
    # Simulate processing
    result['changed'] = True
    result['success'] = True
    result['project_id'] = project_id
    
    if action == 'archive':
        result['message'] = f"Project {project_id} archived successfully"
    elif action == 'delete':
        result['message'] = f"Project {project_id} deleted successfully"
    else:  # notify
        result['message'] = f"Notification sent for project {project_id}"
    
    # Return the results
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
