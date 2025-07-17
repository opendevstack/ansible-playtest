# Parameter Validation Verification Documentation

## Overview

The Parameter Validation Verifier checks that the parameters passed to Ansible modules match expected values. This is crucial for ensuring that modules are not only called the correct number of times but also with the right parameters.

This verifier allows you to validate specific parameter values, ensuring your playbook is passing the correct data to each module.

## Configuration

Configure parameter validation in your scenario YAML under the `verify.parameter_validation` section:

```yaml
verify:
  parameter_validation:
    "module.name":
      - param1: "expected value 1"
        param2: "expected value 2"
      - param1: "different value"
        param2: "for second call"
```

### Structure

- The top-level keys are the fully qualified module names to validate.
- Each module has an array of parameter sets, one for each expected call.
- Each parameter set is an object mapping parameter names to their expected values.
- The order of parameter sets corresponds to the order of module calls.

### Parameters

For each module call, you can specify:

| Parameter | Value |
|-----------|-------|
| Any valid module parameter | The expected value for that parameter |

## How Parameter Validation Works

The verifier:
1. Compares each expected parameter set with the corresponding actual module call
2. Checks that each parameter has the expected value
3. Reports any mismatches in parameter values
4. Fails verification if parameters don't match, if a parameter is missing, or if there are fewer actual calls than expected

## When to Use Parameter Validation

Parameter validation is ideal for:

1. **Data Verification**: Ensuring correct values are passed to modules
2. **End-to-End Testing**: Validating that computed values flow correctly through the playbook
3. **Integration Testing**: Confirming that modules receive the correct data derived from other module outputs
4. **Conditional Logic**: Verifying that parameters change correctly based on playbook conditions

## Example Configurations

### Basic Parameter Validation

```yaml
verify:
  parameter_validation:
    community.general.mail:
      - subject: "Project Notification"
        to: "admin@example.com"
        body: "Project status notification"
```

### Multiple Module Calls

```yaml
verify:
  parameter_validation:
    my.modules.myservice_create_incident:
      - incident_type: "alert"
        priority: "high"
        description: "Critical system failure"
      - incident_type: "request"
        priority: "medium"
        description: "Feature activation request"
```

### Partial Parameter Validation

You can validate just the important parameters without specifying all of them:

```yaml
verify:
  parameter_validation:
    ansible.builtin.template:
      - src: "templates/email_template.j2"
        # Other parameters are not validated
```

## Practical Example

Here's a complete scenario file using parameter validation:

```yaml
name: "Project Email Notification Test"
description: "Tests that email notifications have correct parameters"
playbook: "project_ttl_notification.yaml"

# Mock service responses
service_mocks:
  my.modules.myservice_login:
    success: true
    access_token: "mock-token-value"
    
  # Other mocks...
    
# Verification configuration
verify:
  expected_calls:
    community.general.mail: 1
  
  parameter_validation:
    community.general.mail:
      - to: "project-owner@example.com, project-requestor@example.com"
        subject: "Project BIQ-123 Expiration Notification"
        body_contains: "will be archived in 30 days"
```

## Advanced Features

### Validating Parts of Values

For long text fields like email bodies, you can check that they contain certain substrings:

```yaml
verify:
  parameter_validation:
    community.general.mail:
      - subject_contains: "Expiration"
        body_contains: "will be archived in"
```

Note: The `_contains` suffix is not a built-in feature but a convention that can be implemented in a custom verifier extension.

## Handling Missing Calls

If the parameter validation expects more calls than actually occurred, the verification will fail with a message indicating that the expected call was missing.

## Notes and Best Practices

1. **Validate Important Parameters**: Focus on critical parameters rather than validating everything
2. **Use With Call Count**: Combine with module call count verification for complete testing
3. **Order Matters**: Parameter sets are matched to calls in order, so ensure your expectations match the calling sequence
4. **String Comparison**: Parameter values are compared as strings, so formatting matters
5. **Space Sensitivity**: Leading/trailing whitespace is stripped during comparison

## Troubleshooting

If parameter validation fails:
1. Check the module call details in the playbook statistics
2. Verify that parameter names match exactly, including case
3. Look for whitespace or formatting differences in values
4. Confirm that the expected calls occur in the order specified

## See Also

- [Test Framework Overview](test_framework.md)
- [Module Call Verification](module_call_verifier.md)
- [Call Sequence Verification](sequence_verifier.md)
- [Error Verification](error_verifier.md)
