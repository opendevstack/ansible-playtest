import os
import tempfile
import ansible_runner
from ansible_playtest.module_mocker import ModuleMocker

def main():
    """Example showing how to mock the community.general.file_size module."""
    # Directory for our example
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a mock for the file_size module
        mock_dir = os.path.join(temp_dir, "mocks")
        os.makedirs(mock_dir)
        
        mock_path = os.path.join(mock_dir, "file_size.py")
        with open(mock_path, "w") as f:
            f.write("""
#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule

def main():
    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True),
            size_format=dict(type='str', default='bytes', choices=['bytes', 'kb', 'mb', 'gb']),
        ),
        supports_check_mode=True,
    )

    # Mock always returns 9999 bytes
    result = {
        'changed': False,
        'size': 9999,
        'size_format': module.params['size_format'],
        'path': module.params['path'],
        'size_format_value': 9999 if module.params['size_format'] == 'bytes' else 9.999,
    }
    
    module.exit_json(**result)

if __name__ == '__main__':
    main()
""")
        
        # Create a simple playbook
        playbook_dir = os.path.join(temp_dir, "playbook")
        os.makedirs(playbook_dir)
        
        playbook_path = os.path.join(playbook_dir, "test_file_size.yml")
        with open(playbook_path, "w") as f:
            f.write("""---
- name: Test file size module
  hosts: localhost
  gather_facts: no
  tasks:
    - name: Get file size of a file
      community.general.file_size:
        path: /etc/hosts
      register: file_size_result
      
    - name: Display file size
      debug:
        msg: "File size is {{ file_size_result.size }} bytes"
""")
        
        # Use the ModuleMocker to replace the module
        with ModuleMocker({
            "community.general.file_size": mock_path
        }):
            # Run the playbook with the mocked module
            print(f"Running playbook with mocked community.general.file_size module...")
            runner = ansible_runner.run(
                playbook=playbook_path,
                host_pattern='localhost',
                quiet=False
            )
            
            print(f"Playbook finished with status: {runner.status}")
            
            # The output should show the mocked file size (9999)
            for event in runner.events:
                if event.get('event') == 'runner_on_ok':
                    task = event.get('event_data', {}).get('task')
                    if task == 'Display file size':
                        result = event.get('event_data', {}).get('res', {})
                        print(f"Task result: {result}")
    
    finally:
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()