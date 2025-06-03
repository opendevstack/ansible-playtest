# Call Sequence Verification Documentation

## Overview

The Call Sequence Verifier ensures that Ansible modules are called in the expected order during playbook execution. This is particularly important for workflows where the sequence of operations matters, such as when one task depends on the completion of another.

Unlike module call count verification, which only verifies the total number of calls, sequence verification checks the specific order of calls, ensuring your playbook's logic flows correctly.

## Configuration

Configure call sequence verification in your scenario YAML under the `verify.call_sequence` section:

```yaml
verify:
  call_sequence:
    - "module.name.first"
    - "module.name.second"
    - "module.name.third"
```

### Parameters

The `call_sequence` section takes an array of module names in the order they are expected to be called. Each entry should be a fully qualified module name.

## How Sequence Verification Works

The verifier:
1. Takes the expected sequence of module calls from the scenario configuration
2. Retrieves the actual sequence of calls from playbook statistics
3. Performs non-strict sequence validation (described below)
4. Reports any modules that were called out of order or missing from the sequence

### Non-Strict Sequence Validation

This verifier implements "non-strict" sequence validation, which means:

- Other modules can be called between the modules in your expected sequence
- The expected sequence only needs to be a subsequence of the actual call sequence
- Each module in the expected sequence must appear in the actual sequence, in order

For example, if your expected sequence is `[A, B, C]`, then all of the following actual sequences would pass:
- `[A, B, C]`
- `[A, X, B, Y, C]`
- `[X, A, Y, B, Z, C]`

But these sequences would fail:
- `[A, C, B]` (wrong order)
- `[A, B]` (missing C)
- `[B, C]` (missing A)

## When to Use Sequence Verification

Sequence verification is ideal for:

1. **Workflow Testing**: Ensuring operations happen in the correct order
2. **Dependency Validation**: Verifying prerequisites are performed before dependent tasks
3. **Process Compliance**: Confirming that mandatory steps are performed in sequence
4. **State Management**: Ensuring that state-changing operations happen in the right order

## Example Configurations

### Basic Sequence Verification

```yaml
verify:
  call_sequence:
    - edpc.general.servicenow_login
    - edpc.general.servicenow_retrieve_projects
    - edpc.general.bitbucket_file_retriever
```

### Critical Path Verification

You can focus on just the critical path modules:

```yaml
verify:
  call_sequence:
    - edpc.general.servicenow_login
    - edpc.general.servicenow_retrieve_projects
    - community.general.mail
```

## Practical Example

Here's a complete scenario file using call sequence verification:

```yaml
name: "Project Notification Flow Test"
description: "Tests the sequence of operations in the notification process"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  edpc.general.servicenow_login:
    success: true
    access_token: "mock-token-value"
    
  edpc.general.servicenow_retrieve_projects:
    success: true
    projects:
      - id: "123"
        name: "Test Project"
        
  edpc.general.bitbucket_file_retriever:
    success: true
    exists: true
    content: "[]"
    
# Verification configuration
verify:
  call_sequence:
    - edpc.general.servicenow_login
    - edpc.general.servicenow_retrieve_projects
    - edpc.general.bitbucket_file_retriever
    - ansible.builtin.template
    - community.general.mail
```

## Combining Verifiers

Sequence verification works well when combined with other verifiers:

```yaml
verify:
  # Verify exact call counts
  expected_calls:
    edpc.general.servicenow_login: 1
    community.general.mail: 2
  
  # Verify parameters for specific calls
  parameter_validation:
    community.general.mail:
      - to: "admin@example.com"
        subject: "First Notification"
      
  # Verify call order
  call_sequence:
    - edpc.general.servicenow_login
    - edpc.general.servicenow_retrieve_projects
    - community.general.mail
```

## Notes and Best Practices

1. **Focus on Key Modules**: Include only the modules where order matters
2. **Combine with Other Verifiers**: Use with call count and parameter validation for thorough testing
3. **Consider Branches**: Separate sequence verifications for different execution paths
4. **Handle Conditionals**: Be aware of conditional tasks that may affect sequence
5. **Don't Over-Specify**: Don't include every module call in the sequence unless truly necessary

## Troubleshooting

If sequence verification fails:
1. Check the reported missing modules in the error messages
2. Review the expected vs. actual sequences displayed in the test output
3. Look for conditional tasks that might be altering the execution path
4. Consider if error handling is affecting the module call sequence

## See Also

- [Test Framework Overview](test_framework.md)
- [Module Call Verification](module_call_verifier.md)
- [Parameter Validation](parameter_verifier.md)
- [Error Verification](error_verifier.md)
