# Error Verification Documentation

## Overview

The Error Verifier component checks for expected errors during playbook execution. It validates that specific error messages appear in the expected tasks and that the playbook's overall failure/success status matches expectations.

This verifier is particularly useful for testing error handling, failure scenarios, and ensuring that important error messages are properly raised.

## Configuration

Configure error verification in your scenario YAML under the `verify.expected_errors` section:

```yaml
verify:
  expected_errors:
    - message: "Error message to match"
      task: "Task name where error should occur" # Optional
      expect_process_failure: true|false # Optional, default is false
```

### Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `message` | Yes | The error message text to look for in actual errors. The verifier checks if this text is contained in the actual error message. |
| `task` | No | The name of the task where the error is expected to occur. If provided, the verifier checks that the error happened in this specific task. |
| `expect_process_failure` | No | Set to `true` if you expect the overall playbook to fail due to this error. Default is `false`. |

## Behavior in Different Scenarios

### 1. Task fails and playbook fails

Configuration:
```yaml
expected_errors:
  - message: "Authorization failed"
    task: "Get the access token"
    expect_process_failure: true
```

Behavior:
- The verifier checks if an error containing "Authorization failed" occurred in the "Get the access token" task
- It also verifies that the playbook failed overall
- All conditions must be met for the verification to PASS

### 2. Task fails but playbook handles the error

Configuration:
```yaml
expected_errors:
  - message: "Resource not found"
    task: "Retrieve resource"
    expect_process_failure: false
```

Behavior:
- The verifier checks if an error containing "Resource not found" occurred in the "Retrieve resource" task
- It verifies that the playbook didn't fail overall (error was properly handled)
- This is useful for testing error handling logic in playbooks

### 3. Task doesn't fail when it should

Configuration:
```yaml
expected_errors:
  - message: "Expected validation error"
    task: "Validate data"
    expect_process_failure: true|false
```

Behavior:
- If the task doesn't raise the expected error, the verification will FAIL
- The verifier will report that the expected error wasn't found
- This is useful for verifying that validation logic properly catches issues

### 4. No errors expected

Simply don't include `expected_errors` in your verification configuration if you expect the playbook to run without errors.

## Example Scenarios

### Basic Error Checking

```yaml
verify:
  expected_errors:
    - message: "Service unavailable"
      task: "Call external API"
      expect_process_failure: true
```

### Multiple Expected Errors

```yaml
verify:
  expected_errors:
    - message: "Invalid credentials"
      task: "Authenticate to service"
      expect_process_failure: true
    - message: "Cannot proceed without authentication"
      task: "Perform protected operation"
      expect_process_failure: false
```

### Error Without Task Specification

```yaml
verify:
  expected_errors:
    - message: "Resource limit exceeded"
      expect_process_failure: true
```

## Practical Example

Here's a complete scenario file using error verification to test ServiceNow login failure:

```yaml
name: "Project Notification Test - ServiceNow Login Failure"
description: "Tests notification process error handling when ServiceNow login fails"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  edpc.general.servicenow_login:
    success: false
    error_message: "Invalid credentials or authorization failed"
    status_code: 401
    
  # Other mocks...
    
# Expected function calls with parameters
verify:
  expected_calls:
    edpc.general.servicenow_login: 1
    edpc.general.servicenow_retrieve_projects: 0
  
  # Error verification configuration
  expected_errors:
    - message: "Unknown error"
      task: "Get the access token for servicenow."
      expect_process_failure: true
```

## Notes and Best Practices

1. Be specific with error messages to avoid false positives
2. Include task names when multiple similar errors might appear
3. Use `expect_process_failure` to verify proper error handling or failure propagation
4. For conditional errors, create separate scenario files for each condition
5. Combine with module call verification to ensure no unexpected calls happen after errors

## See Also

- [Test Framework Overview](test_framework.md)
- [Module Call Verification](module_call_verifier.md)
- [Parameter Validation](parameter_verifier.md)
- [Call Sequence Verification](sequence_verifier.md)
