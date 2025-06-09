#!/usr/bin/python

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: file_size
short_description: Mocked version of community.general.filesize module
description:
    - Mocked implementation that returns predefined values
author: "Mocked Author (@mock)"
options:
  path:
    description:
      - Path of the regular file to create or resize.
    type: path
    required: true

  size:
    description:
      - Requested size of the file.
    type: raw
    required: true    
'''

EXAMPLES = '''
- name: Create size of /path/to/file
  community.general.filesize:
    path: /path/to/file
  register: file_size_result
'''

RETURN = '''
size:
    description: File size in bytes
    returned: success
    type: int
    sample: 1024
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    # Use a real AnsibleModule with empty argument_spec to accept any parameters
    module = AnsibleModule(
        argument_spec={},  # Empty dict - will accept any parameter
        supports_check_mode=True,
        bypass_checks=True  # Skip parameter validation
    )
    
    # Get path parameter or use default
    path = module.params.get('path', '/mocked/path')
    
    # Return mocked values
    result = {
        'changed': True,
        'size': 1024,  # Mocked file size (1KB)
        'path': path
    }
    
    # This will properly exit the module
    module.exit_json(**result)


if __name__ == '__main__':
    main()
