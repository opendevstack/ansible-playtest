# Creating Test Scenarios

Test scenarios are the heart of the AnsiblePlayTest framework. They define what your playbook should do, how external services should behave, and what the expected outcomes are. This guide covers everything you need to know about creating effective test scenarios.

## Table of Contents

- [Scenario File Structure](#scenario-file-structure)
- [Basic Scenario Elements](#basic-scenario-elements)
- [Service Mocking](#service-mocking)
- [Verification Strategies](#verification-strategies)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Common Patterns](#common-patterns)
- [Examples](#examples)

## Scenario File Structure

A test scenario is a YAML file that defines:

1. **Metadata**: Basic information about the scenario
2. **Service Mocks**: How external services should behave
3. **Verification**: What to validate after the playbook runs

### Basic Template

```yaml
---
name: "Your Scenario Name"
description: "A clear description of what this scenario tests"
playbook: "your_playbook.yml"

# Optional: Mock external services
service_mocks:
  # Module mocks go here

# Required: Define what to verify
verify:
  # Verification criteria go here
```

## Basic Scenario Elements

### Required Fields

| Field | Description | Example |
|-------|-------------|---------|
| `name` | A descriptive name for the scenario | `"User Authentication Test"` |
| `description` | Detailed explanation of what's being tested | `"Tests successful user login with valid credentials"` |
| `playbook` | The playbook file to execute (relative to playbook directory) | `"user_management.yml"` |

### Optional Fields

| Field | Description | Example |
|-------|-------------|---------|
| `service_mocks` | Mock responses for external services | See [Service Mocking](#service-mocking) |
| `verify` | Verification criteria for the test | See [Verification Strategies](#verification-strategies) |

## Service Mocking

Service mocks allow you to simulate external dependencies without actually calling them. This ensures tests are fast, reliable, and don't have side effects.

### Basic Mock Structure

```yaml
service_mocks:
  "module.name":
    # Simple mock response
    success: true
    changed: false
    result: "Mock response"
```

### Mock Response Fields

| Field | Description | Example |
|-------|-------------|---------|
| `success` | Whether the module succeeds | `true` or `false` |
| `changed` | Whether the module reports changes | `true` or `false` |
| `failed` | Whether the module fails | `true` or `false` |
| Any other field | Custom return values | `message: "Custom response"` |

### Multiple Response Variations

You can define different responses for different conditions:

```yaml
service_mocks:
  "ansible.builtin.uri":
    - task_parameters:
        url: "https://api.example.com/users"
      success: true
      status: 200
      json:
        users: ["alice", "bob"]
    
    - task_parameters:
        url: "https://api.example.com/error"
      success: false
      status: 500
      msg: "Internal server error"
```

### Complex Mock Examples

#### API Service Mock
```yaml
service_mocks:
  "ansible.builtin.uri":
    success: true
    changed: false
    status: 200
    json:
      id: 123
      name: "Test User"
      email: "test@example.com"
    headers:
      content-type: "application/json"
```

#### File Operations Mock
```yaml
service_mocks:
  "ansible.builtin.copy":
    success: true
    changed: true
    dest: "/tmp/test_file.txt"
    size: 1024
    mode: "0644"
```

#### Custom Module Mock
```yaml
service_mocks:
  "mycompany.mymodule.custom_processor":
    success: true
    changed: true
    message: "Processing completed successfully"
    processed_items: 42
    processing_time: "2.5s"
```

## Verification Strategies

The `verify` section defines what aspects of the playbook execution to validate. You can combine multiple verification strategies for comprehensive testing.

### Module Call Count Verification

Verify that modules are called the expected number of times:

```yaml
verify:
  expected_calls:
    "ansible.builtin.ping": 1
    "ansible.builtin.debug": 3
    "ansible.builtin.copy": 2
    "custom.module": 0  # Should not be called
```

### Parameter Validation

Verify that modules receive the correct parameters:

```yaml
verify:
  parameter_validation:
    ansible.builtin.copy:
      - src: "/source/file.txt"
        dest: "/destination/file.txt"
        mode: "0644"
      - content: "Hello, World!"
        dest: "/tmp/hello.txt"
    
    ansible.builtin.debug:
      - msg: "Processing complete"
        var: result
```

### Call Sequence Verification

Ensure modules are called in the expected order:

```yaml
verify:
  call_sequence:
    - "ansible.builtin.ping"
    - "ansible.builtin.uri"
    - "ansible.builtin.copy"
    - "ansible.builtin.debug"
```

### Error Verification

Test error handling and failure scenarios:

```yaml
verify:
  expected_errors:
    - message: "Authentication failed"
      task: "Login to service"
      expect_process_failure: true
    
    - message: "Resource not found"
      task: "Fetch data"
      expect_process_failure: false  # Error handled gracefully
```

## Advanced Features

### Conditional Mocks

Create different scenarios for different conditions:

#### Success Scenario
```yaml
name: "Successful API Call"
service_mocks:
  "ansible.builtin.uri":
    success: true
    status: 200
    json: { "status": "ok" }

verify:
  expected_calls:
    "ansible.builtin.uri": 1
  expected_errors: []
```

#### Failure Scenario
```yaml
name: "Failed API Call"
service_mocks:
  "ansible.builtin.uri":
    success: false
    status: 500
    msg: "Internal server error"

verify:
  expected_calls:
    "ansible.builtin.uri": 1
  expected_errors:
    - message: "Internal server error"
      expect_process_failure: true
```

### Multi-Call Mocks

For modules called multiple times with different parameters:

```yaml
service_mocks:
  "ansible.builtin.copy":
    - task_parameters:
        dest: "/tmp/file1.txt"
      success: true
      changed: true
    
    - task_parameters:
        dest: "/tmp/file2.txt"
      success: true
      changed: false  # File already exists
```

### Environment-Specific Scenarios

Create scenarios for different environments:

```yaml
name: "Production Deployment"
description: "Tests deployment to production environment"
playbook: "deploy.yml"

# Production-specific mocks
service_mocks:
  "ansible.builtin.uri":
    success: true
    status: 200
    json:
      environment: "production"
      version: "1.2.3"

verify:
  parameter_validation:
    ansible.builtin.template:
      - dest: "/etc/app/config.conf"
        backup: true
  
  expected_calls:
    "ansible.builtin.service": 1  # Restart service
```

## Best Practices

### 1. Descriptive Naming

Use clear, descriptive names for scenarios:

✅ **Good:**
```yaml
name: "User Registration - Valid Email Format"
description: "Tests user registration with properly formatted email address"
```

❌ **Avoid:**
```yaml
name: "Test 1"
description: "Basic test"
```

### 2. Focus on Single Responsibility

Each scenario should test one specific behavior:

✅ **Good:**
```yaml
name: "Email Notification - Success Path"
# Tests only the successful email sending
```

❌ **Avoid:**
```yaml
name: "Complete User Workflow"
# Tests registration, login, profile update, and deletion
```

### 3. Mock Only What's Necessary

Mock external dependencies, but don't over-mock:

✅ **Good:**
```yaml
service_mocks:
  "ansible.builtin.uri":  # External API call
    status: 200
    json: { "result": "success" }
  
  # Don't mock ansible.builtin.debug - it's harmless
```

### 4. Verify Critical Behaviors

Focus verification on the most important aspects:

✅ **Good:**
```yaml
verify:
  expected_calls:
    "critical.module": 1  # Must be called
  
  parameter_validation:
    critical.module:
      - important_param: "expected_value"
```

### 5. Use Meaningful Mock Data

Make mock data realistic and relevant:

✅ **Good:**
```yaml
service_mocks:
  "user.service.get_user":
    id: "user123"
    name: "John Doe"
    email: "john.doe@example.com"
    role: "admin"
```

❌ **Avoid:**
```yaml
service_mocks:
  "user.service.get_user":
    id: "123"
    name: "test"
    data: "foo"
```

## Common Patterns

### Testing Different User Roles

Create scenarios for different user permissions:

```yaml
# admin_scenario.yml
name: "Admin User Actions"
service_mocks:
  "auth.check_permissions":
    user_role: "admin"
    can_delete: true
    can_modify: true

verify:
  expected_calls:
    "admin.delete_user": 1
```

```yaml
# user_scenario.yml
name: "Regular User Actions"
service_mocks:
  "auth.check_permissions":
    user_role: "user"
    can_delete: false
    can_modify: false

verify:
  expected_calls:
    "admin.delete_user": 0  # Should not be called
  expected_errors:
    - message: "Insufficient permissions"
```

### Testing API Integration

```yaml
name: "API Integration - Success Path"
service_mocks:
  "ansible.builtin.uri":
    status: 200
    json:
      data: [
        { "id": 1, "name": "Item 1" },
        { "id": 2, "name": "Item 2" }
      ]

verify:
  parameter_validation:
    ansible.builtin.uri:
      - url: "https://api.example.com/items"
        method: "GET"
        headers:
          Authorization: "Bearer {{ api_token }}"
```

## Examples

### Complete Email Notification Scenario

```yaml
---
name: "Email Notification - Success Path"
description: "Tests successful email notification with SMTP server"
playbook: "send_notification.yml"

service_mocks:
  # Mock user lookup
  "ldap.lookup_user":
    success: true
    user:
      name: "John Doe"
      email: "john.doe@example.com"
      department: "Engineering"
  
  # Mock template rendering
  "ansible.builtin.template":
    success: true
    changed: true
    dest: "/tmp/email_body.html"

verify:
  expected_calls:
    "ldap.lookup_user": 1
    "ansible.builtin.template": 1
    "community.general.mail": 1
  
  parameter_validation:
    community.general.mail:
      - to: "john.doe@example.com"
        subject: "Welcome to the System"
        body: "{{ email_body }}"
        host: "localhost"
        port: 1025
  
  call_sequence:
    - "ldap.lookup_user"
    - "ansible.builtin.template"
    - "community.general.mail"
```

### Database Migration Scenario

```yaml
---
name: "Database Migration - Version Upgrade"
description: "Tests database schema migration from v1.0 to v1.1"
playbook: "database_migration.yml"

service_mocks:
  # Mock current version check
  "database.get_version":
    current_version: "1.0"
    needs_migration: true
  
  # Mock backup operation
  "database.backup":
    success: true
    backup_file: "/backups/db_backup_20240122.sql"
    size_mb: 250
  
  # Mock migration execution
  "database.run_migration":
    success: true
    migration_file: "v1.0_to_v1.1.sql"
    rows_affected: 15420
    duration_seconds: 45

verify:
  expected_calls:
    "database.get_version": 1
    "database.backup": 1
    "database.run_migration": 1
    "database.verify_migration": 1
  
  parameter_validation:
    database.backup:
      - backup_name: "pre_migration_{{ ansible_date_time.date }}"
    
    database.run_migration:
      - migration_script: "migrations/v1.0_to_v1.1.sql"
        dry_run: false
  
  call_sequence:
    - "database.get_version"
    - "database.backup"
    - "database.run_migration"
    - "database.verify_migration"
```

## Next Steps

Now that you understand how to create scenarios, explore these related topics:

- **[Verification Strategies](verifier_overview.md)** - Deep dive into verification options
- **[Configuration Options](configuration.md)** - Advanced configuration features
- **[Using Verifiers](verifiers.md)** - Detailed verifier documentation
- **[Mock SMTP Server](mock_smtp_server.md)** - Testing email functionality
- **[Best Practices](verifier_examples.md)** - Advanced patterns and examples

## See Also

- [Getting Started Guide](getting_started.md) - Basic setup and first tests
- [Verifier Examples](verifier_examples.md) - More verification examples
- [Module Call Verifier](module_call_verifier.md) - Call count verification
- [Parameter Verifier](parameter_verifier.md) - Parameter validation
- [Sequence Verifier](sequence_verifier.md) - Call order verification
- [Error Verifier](error_verifier.md) - Error handling verification
