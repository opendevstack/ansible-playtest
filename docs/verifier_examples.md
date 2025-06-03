# Verifier Examples and Best Practices

This document provides practical examples and best practices for using the verification strategies in the test framework.

## Example Scenarios

### Basic Success Path Testing

This example demonstrates a basic success path test scenario that uses all four verifiers:

```yaml
name: "Project Notification Test - Success Path"
description: "Tests successful project notification workflow"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  edpc.general.servicenow_login:
    success: true
    access_token: "mock-token-value"
    
  edpc.general.servicenow_retrieve_projects:
    success: true
    projects:
      - id: "PROJ-123"
        name: "Test Project"
        owner: "project.owner@example.com"
        requestor: "project.requestor@example.com"
        created_date: "${DATE:-60}"
        status: "active"
        
  edpc.general.bitbucket_file_retriever:
    success: true
    exists: true
    content: '[]'
    
  edpc.general.bitbucket_file_upload:
    success: true
    
# Verification configuration
verify:
  # Verify module call counts
  expected_calls:
    edpc.general.servicenow_login: 1
    edpc.general.servicenow_retrieve_projects: 1
    edpc.general.bitbucket_file_retriever: 1
    edpc.general.bitbucket_file_upload: 1
    community.general.mail: 2
  
  # Verify parameters
  parameter_validation:
    community.general.mail:
      - to: "project.owner@example.com,project.requestor@example.com"
        subject: "Project PROJ-123 Expiration Notification"
    
    edpc.general.bitbucket_file_upload:
      - content_contains: "PROJ-123"
  
  # Verify call sequence
  call_sequence:
    - edpc.general.servicenow_login
    - edpc.general.servicenow_retrieve_projects
    - edpc.general.bitbucket_file_retriever
    - edpc.general.bitbucket_file_upload
    - community.general.mail
```

### Error Handling Testing

This example demonstrates testing error handling and recovery:

```yaml
name: "Project Notification Test - ServiceNow Error Recovery"
description: "Tests recovery when ServiceNow API initially fails"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  edpc.general.servicenow_login:
    _conditional_responses:
      - condition:
          _call_count: 1
        response:
          success: false
          error_message: "Service temporarily unavailable"
      - condition:
          _call_count: 2
        response:
          success: true
          access_token: "mock-token-value"
    
  # Other mocks...
    
# Verification configuration
verify:
  # Verify module call counts - login called twice due to retry
  expected_calls:
    edpc.general.servicenow_login: 2
    edpc.general.servicenow_retrieve_projects: 1
  
  # Verify error occurred but was handled
  expected_errors:
    - message: "Service temporarily unavailable"
      task: "Get the access token for servicenow"
      expect_process_failure: false
```

### Complex Parameter Validation

This example shows more complex parameter validation:

```yaml
name: "Project Deletion Test - Complex Parameters"
description: "Tests complex parameter validation in deletion workflow"
playbook: "project_deletion.yaml"

service_mocks:
  # Mock responses...

verify:
  parameter_validation:
    edpc.general.servicenow_update_project:
      - project_id: "PROJ-123"
        fields:
          status: "deleted"
          deletion_date: "${TODAY}"
          deleted_by: "automation"
          
    community.general.mail:
      - to: "{{ lookup('env', 'ADMIN_EMAIL') }}"
        subject: "Project Deletion Report"
        body_contains:
          - "Successfully deleted: 1"
          - "PROJ-123"
          - "Failures: 0"
```

## Best Practices by Verification Type

### Module Call Verification

1. **Verify only what matters**: Only include modules critical to the scenario
2. **Be explicit about zero calls**: For modules that should NOT be called, explicitly set the count to 0
3. **Check external integrations**: Always verify calls to external services

Example:
```yaml
verify:
  expected_calls:
    edpc.general.servicenow_login: 1
    edpc.general.servicenow_create_incident: 0  # Should not create an incident in this scenario
    community.general.mail: 1
```

### Parameter Validation

1. **Focus on critical parameters**: Verify only the most important parameters
2. **Check computed values**: Validate parameters that result from computations
3. **Use partial matching**: For large text fields, check for key content rather than exact matches

Example:
```yaml
verify:
  parameter_validation:
    community.general.mail:
      - subject_contains: "Expiration"
        body_contains: 
          - "will be deleted on"
          - "${DATE:+30}"  # Using dynamic date
```

### Call Sequence Verification

1. **Focus on dependencies**: Verify sequence for operations with dependencies
2. **Keep it simple**: Only include critical modules in sequence verification
3. **Account for branching**: Create different scenarios for different execution paths

Example:
```yaml
verify:
  call_sequence:
    - edpc.general.servicenow_login  # Must happen first
    - edpc.general.servicenow_retrieve_projects  # Depends on login
    - edpc.general.bitbucket_file_upload  # Must happen after project retrieval
```

### Error Verification

1. **Be specific with error messages**: Use unique parts of error messages to avoid false matches
2. **Test both failure and recovery**: Verify both that errors occur and that they're handled
3. **Check overall process impact**: Use `expect_process_failure` to validate if errors are fatal

Example:
```yaml
verify:
  expected_errors:
    - message: "Access denied: insufficient permissions"
      task: "Update ServiceNow record"
      expect_process_failure: true  # This should be a fatal error
```

## Common Test Patterns

### Testing Conditional Logic

For testing branches in code:

```yaml
# Scenario 1: When condition is true
extra_vars:
  feature_enabled: true

verify:
  expected_calls:
    module.for.feature: 1

# Scenario 2: When condition is false
extra_vars:
  feature_enabled: false

verify:
  expected_calls:
    module.for.feature: 0
```

### Testing Looping Constructs

For testing loops:

```yaml
# Mock data with 3 items to process
service_mocks:
  retrieve.items:
    items:
      - id: "item1"
      - id: "item2" 
      - id: "item3"

verify:
  expected_calls:
    process.item: 3  # Should be called once per item
  
  parameter_validation:
    process.item:
      - id: "item1"  # First call
      - id: "item2"  # Second call
      - id: "item3"  # Third call
```

### Testing Error Recovery

For testing recovery from temporary failures:

```yaml
service_mocks:
  api.call:
    _conditional_responses:
      - condition:
          _call_count: 1
        response:
          success: false
          error: "Temporary failure"
      - condition:
          _call_count: 2
        response:
          success: true
          data: "Success on retry"

verify:
  expected_calls:
    api.call: 2  # Called twice due to retry
  expected_errors:
    - message: "Temporary failure"
      expect_process_failure: false  # Process should recover
```

## Integration with Mock SMTP Server

For email verification:

```yaml
# Configuration to capture and verify emails
verify:
  # Verify email module calls
  expected_calls:
    community.general.mail: 2
  
  # Verify email parameters
  parameter_validation:
    community.general.mail:
      - to: "admin@example.com"
        subject: "First notification"
      - to: "user@example.com"
        subject: "Second notification"
```

## See Also

- [Verifier Overview](verifier_overview.md)
- [Module Call Verifier](module_call_verifier.md)
- [Parameter Verifier](parameter_verifier.md)
- [Sequence Verifier](sequence_verifier.md)
- [Error Verifier](error_verifier.md)
- [Test Framework Documentation](test_framework.md)
