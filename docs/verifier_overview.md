# Verification Strategies Overview

## Introduction

Verification strategies are essential components of the test framework that validate different aspects of playbook execution. Each strategy focuses on a specific validation area and can be combined to create comprehensive test scenarios.

This document provides an overview of all available verification strategies and links to detailed documentation for each one.

## Available Verification Strategies

| Verifier | Purpose | Documentation |
|----------|---------|---------------|
| **Module Call Count** | Verifies that modules are called the expected number of times | [Module Call Verifier](module_call_verifier.md) |
| **Parameter Validation** | Checks that parameters passed to modules match expected values | [Parameter Verifier](parameter_verifier.md) |
| **Call Sequence** | Validates that modules are called in the expected order | [Sequence Verifier](sequence_verifier.md) |
| **Error Verification** | Checks for expected errors in tasks and validates error handling | [Error Verifier](error_verifier.md) |

## Configuring Verifiers

All verifiers are configured in the test scenario YAML files under the `verify` section. Here's a comprehensive example showing the configuration of all verifiers:

```yaml
verify:
  # Module call count verification
  expected_calls:
    my.modules.myservice_login: 1
    my.modules.myservice_retrieve_projects: 1
    community.general.mail: 2
    ansible.builtin.template: 1
  
  # Parameter validation
  parameter_validation:
    community.general.mail:
      - subject: "Project Expiration Notice"
        to: "admin@example.com"
        body_contains: "will expire in 30 days"
      - subject: "Project Expiration Confirmation"
        to: "admin@example.com,manager@example.com"
  
  # Call sequence verification
  call_sequence:
    - my.modules.myservice_login
    - my.modules.myservice_retrieve_projects
    - ansible.builtin.template
    - community.general.mail
  
  # Error verification
  expected_errors:
    - message: "Service unavailable"
      task: "Call external API"
      expect_process_failure: false
```

## Verification Execution

During test execution, each configured verifier evaluates the playbook results against the specified expectations:

1. **Module Call Count Verifier**: Counts the occurrences of each module call and compares with expected values
2. **Parameter Validator**: Examines the parameters passed to modules against the expected values
3. **Sequence Verifier**: Checks the order of module calls against the expected sequence
4. **Error Verifier**: Validates that expected errors occurred in specified tasks

Each verifier produces a detailed report showing pass/fail status and any discrepancies found.

## Combining Verifiers

Verifiers can be combined to create comprehensive test scenarios that validate multiple aspects of playbook execution. For example:

- Use **Module Call Count** and **Parameter Validation** to verify both the number of calls and the parameters passed
- Combine **Call Sequence** and **Error Verification** to ensure operations happen in the correct order and errors are properly handled
- Use all verifiers together for complete end-to-end testing of complex workflows

## Adding Custom Verifiers

The test framework allows for extending the verification capabilities by creating custom verifiers:

1. Create a new verifier class in the `tests/verifiers` directory that extends `VerificationStrategy`
2. Implement the required methods: `verify()`, `get_status()`, and any helper methods
3. Update the `VerificationStrategyFactory` to include the new verifier
4. Add appropriate configuration to your test scenarios

For detailed implementation instructions, see the [Test Framework Documentation](test_framework.md#creating-custom-verification-strategies).

## Best Practices for Verification

1. **Start Simple**: Begin with module call verification, then add more complex validations
2. **Verify Critical Paths**: Focus verifications on the most critical aspects of your playbook
3. **Combine Strategies**: Use multiple verification strategies to validate different aspects
4. **Keep Scenarios Focused**: Each scenario should test a specific function or code path
5. **Document Expectations**: Add clear descriptions to your test scenarios explaining what's being verified

For practical examples and common test patterns, see the [Verifier Examples and Best Practices](verifier_examples.md) document.

## See Also

- [Test Framework Overview](test_framework.md)
- [Mock SMTP Server](mock_smtp_server.md) - For email verification
- [Creating Test Scenarios](test_framework.md#creating-test-scenarios)
