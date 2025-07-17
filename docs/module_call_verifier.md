# Module Call Count Verification Documentation

## Overview

The Module Call Count Verifier checks that Ansible modules in your playbook are called the expected number of times. This is crucial for ensuring that automation flows execute the correct operations in the right quantity.

For example, you might want to verify that an email module is called exactly once, or that a database update module is never called in a read-only scenario.

## Configuration

Configure module call count verification in your scenario YAML file under the `verify.expected_calls` section:

```yaml
verify:
  expected_calls:
    "module.name.one": 1
    "module.name.two": 2
    "module.name.three": 0
```

### Parameters

| Module Name | Call Count |
|-------------|------------|
| Fully qualified module name | Expected number of times the module should be called |

The verifier will compare the actual number of calls for each module with the expected count specified in your configuration. Any discrepancy will result in verification failure.

## When to Use Module Call Verification

Module call count verification is useful for:

1. **Functional Testing**: Ensuring core modules are called the expected number of times
2. **Regression Testing**: Detecting when changes cause extra or missing module calls
3. **Edge Case Testing**: Verifying modules are not called in specific scenarios
4. **Error Handling**: Confirming that modules are skipped when errors occur

## Example Configurations

### Basic Verification

```yaml
verify:
  expected_calls:
    awx.awx.job_template_launch: 1
    community.general.mail: 1
```

### Verifying Modules Are Not Called

```yaml
verify:
  expected_calls:
    community.general.mail: 0  # Verify email is NOT sent
    ansible.builtin.file: 0  # Verify no files are created/modified
```

### Comprehensive Module Call Verification

```yaml
verify:
  expected_calls:
    my.modules.myservice_login: 1
    my.modules.myservice_retrieve_projects: 1
    my.modules.myrepository_file_retriever: 1
    community.general.mail: 3
    ansible.builtin.template: 2
```

## Practical Example

Here's a complete scenario file with module call count verification:

```yaml
name: "Project Notification Test - Basic Flow"
description: "Tests basic project notification workflow"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  my.modules.myservice_login:
    success: true
    access_token: "mock-token-value"
    
  my.modules.myservice_retrieve_projects:
    success: true
    projects:
      - id: "123"
        name: "Test Project"
        
  my.modules.myrepository_file_retriever:
    success: true
    exists: true
    content: "[]"
    
# Verification configuration
verify:
  expected_calls:
    my.modules.myservice_login: 1
    my.modules.myservice_retrieve_projects: 1
    my.modules.myrepository_file_retriever: 1
    community.general.mail: 1
```

## How Verification Works

The verifier:
1. Extracts expected call counts from the scenario configuration
2. Retrieves actual call counts from playbook statistics
3. Compares expected vs. actual calls for each module
4. Reports any discrepancies in counts
5. Returns an overall pass/fail status

If any module's actual call count differs from the expected count, the verification fails and details about the mismatch are displayed.

## Notes and Best Practices

1. **Be specific**: Only verify module calls that are critical to the scenario
2. **Zero verification**: Explicitly verify 0 calls when a module should NOT be called
3. **Combine verifiers**: Use with parameter validation to check both call count and parameters
4. **Include all modules**: Make sure all important modules are included in your verification
5. **Keep up to date**: Update expected calls when modifying playbook logic

## Troubleshooting

If module call verification fails, check:
1. Playbook logic for unexpected conditional execution
2. Error handling that might skip certain tasks
3. Mock configurations that might trigger different code paths
4. The actual playbook statistics to see which modules were called

## See Also

- [Test Framework Overview](test_framework.md)
- [Parameter Validation](parameter_verifier.md)
- [Call Sequence Verification](sequence_verifier.md)
- [Error Verification](error_verifier.md)
