# Verifier Examples and Best Practices

This document provides practical examples and best practices for using the verification strategies in the test framework.

## YAML Structure

Test scenarios support two mock configuration formats:
- `service_mocks:` - For general module mocking
- `mocks:` - Alternative format with module/responses structure

Both formats are supported and can be used interchangeably.

## Example Scenarios

### Basic Success Path Testing

This example demonstrates a basic success path test scenario that uses all four verifiers:

```yaml
name: "Project Notification Test - Success Path"
description: "Tests successful project notification workflow"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  my.modules.myservice_login:
    success: true
    access_token: "mock-token-value"
    
  my.modules.myservice_retrieve_projects:
    success: true
    projects:
      - id: "PROJ-123"
        name: "Test Project"
        owner: "project.owner@example.com"
        requestor: "project.requestor@example.com"
        created_date: "${DATE:-60}"
        status: "active"
        
  my.modules.myrepository_file_retriever:
    success: true
    exists: true
    content: '[]'
    
  my.modules.myrepository_file_upload:
    success: true
    
# Verification configuration
verify:
  # Verify module call counts
  expected_calls:
    my.modules.myservice_login: 1
    my.modules.myservice_retrieve_projects: 1
    my.modules.myrepository_file_retriever: 1
    my.modules.myrepository_file_upload: 1
    community.general.mail: 2
  
  # Verify parameters
  parameter_validation:
    community.general.mail:
      - to: "project.owner@example.com,project.requestor@example.com"
        subject: "Project PROJ-123 Expiration Notification"
    
    my.modules.myrepository_file_upload:
      - content: "Updated project list: PROJ-123"
  
  # Verify call sequence
  call_sequence:
    - my.modules.myservice_login
    - my.modules.myservice_retrieve_projects
    - my.modules.myrepository_file_retriever
    - my.modules.myrepository_file_upload
    - community.general.mail
```

### Error Handling Testing

This example demonstrates testing error handling:

```yaml
name: "Project Notification Test - MyService Error"
description: "Tests error handling when MyService API fails"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  my.modules.myservice_login:
    success: false
    error_message: "Service temporarily unavailable"
    
  # Other mocks...
    
# Verification configuration
verify:
  # Verify module call counts
  expected_calls:
    my.modules.myservice_login: 1
  
  # Verify error occurred
  expected_errors:
    - message: "Service temporarily unavailable"
      task: "Get the access token for myservice"
      expect_process_failure: true
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
    my.modules.myservice_update_project:
      - project_id: "PROJ-123"
        fields:
          status: "deleted"
          deletion_date: "${TODAY}"
          deleted_by: "automation"
          
    community.general.mail:
      - to: "{{ lookup('env', 'ADMIN_EMAIL') }}"
        subject: "Project Deletion Report"
        body: "Successfully deleted: 1 projects. PROJ-123 completed. Failures: 0"
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
    my.modules.myservice_login: 1
    my.modules.myservice_create_incident: 0  # Should not create an incident in this scenario
    community.general.mail: 1
```

### Parameter Validation

1. **Focus on critical parameters**: Verify only the most important parameters
2. **Check computed values**: Validate parameters that result from computations
3. **Use exact matching**: Parameter validation uses exact string comparison

**Note**: Advanced parameter validation features like `subject_contains` or `body_contains` are not currently implemented. Use exact parameter values for validation.

Example:
```yaml
verify:
  parameter_validation:
    community.general.mail:
      - subject: "Project Expiration Notification"
        to: "admin@example.com"
        body: "Project will be deleted on 2024-01-01"
```

### Call Sequence Verification

1. **Focus on dependencies**: Verify sequence for operations with dependencies
2. **Keep it simple**: Only include critical modules in sequence verification
3. **Account for branching**: Create different scenarios for different execution paths

Example:
```yaml
verify:
  call_sequence:
    - my.modules.myservice_login  # Must happen first
    - my.modules.myservice_retrieve_projects  # Depends on login
    - my.modules.myrepository_file_upload  # Must happen after project retrieval
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
      task: "Update MyService record"
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

For testing error scenarios (note: conditional responses based on call count are not currently implemented):

```yaml
# Mock a service that always fails
service_mocks:
  api.call:
    success: false
    error: "Service unavailable"

verify:
  expected_calls:
    api.call: 1
  expected_errors:
    - message: "Service unavailable"
      expect_process_failure: true  # Process should fail
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
