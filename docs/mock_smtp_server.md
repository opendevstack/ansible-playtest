# Mock SMTP Server

This document describes how to use the Mock SMTP Server for testing email functionality.

## Overview

The Mock SMTP Server is implemented using Python's `smtpd` and `asyncore` libraries, providing a lightweight SMTP server for testing. It supports:

- Email reception and storage for verification in tests
- Detailed logging of server activity and message statistics
- Command-line interface for standalone operation
- Context manager support for test integration
- Thread-safe operation with proper startup and shutdown sequences

## Installation

The mock SMTP server is included in the test suite. To use it, you need the standard Python libraries:

```bash
pip install -r test-requirements.txt
```

## Running the Mock SMTP Server

### Command Line Usage

A command-line utility is provided to run the mock SMTP server:

```bash
# Basic usage (defaults to localhost:1025)
python3 tests/mock_smtp_server.py

# Run with specific port
python3 tests/mock_smtp_server.py --port 2525

# Run with specific host
python3 tests/mock_smtp_server.py --host 0.0.0.0

# Run with verbose logging
python3 tests/mock_smtp_server.py --verbose
```

When running in command-line mode, the server will display statistics periodically and show information about each received message. Press Ctrl+C to stop the server and display final statistics.

### Command Line Options

| Option | Description |
|--------|-------------|
| `--host` | Hostname to bind the server to (default: localhost) |
| `--port` | Port to bind the server to (default: 1025) |
| `--verbose` or `-v` | Enable verbose logging |

## Using in Python Code

### Basic Usage

```python
from tests.mock_smtp_server import MockSMTPServer

# Start server with default settings (localhost:1025)
server = MockSMTPServer()
server.start()

# Use the server (e.g., send emails to it)
# ...

# Get received messages
messages = server.get_messages()
for msg in messages:
    print(f"From: {msg['mail_from']}, To: {msg['rcpt_tos']}")
    print(f"Content: {msg['data']}")

# Stop the server when done
server.stop()
```

### Using as Context Manager

```python
from tests.mock_smtp_server import MockSMTPServer

with MockSMTPServer(port=2525) as server:
    # Server is started automatically
    
    # Use the server (e.g., send emails to it)
    # ...
    
    # Get received messages
    messages = server.get_messages()
    
    # Server is stopped automatically when exiting the context
```

### Configuration Options

```python
# Configuration example
server = MockSMTPServer(
    host='0.0.0.0',  # Listen on all interfaces
    port=2525,       # Use port 2525
    verbose=True     # Enable verbose logging
)
```

## Example: Testing with smtplib

```python
import smtplib
from email.message import EmailMessage
from tests.mock_smtp_server import MockSMTPServer

# Start the server
with MockSMTPServer() as server:
    # Create and send an email
    msg = EmailMessage()
    msg['Subject'] = 'Test Email'
    msg['From'] = 'sender@example.com'
    msg['To'] = 'recipient@example.com'
    msg.set_content('This is a test email')
    
    # Connect to the server
    smtp = smtplib.SMTP('localhost', 1025)
    
    # Send email
    smtp.send_message(msg)
    smtp.quit()
    
    # Verify message was received
    messages = server.get_messages()
    assert len(messages) == 1
    assert messages[0]['mail_from'] == 'sender@example.com'
```

## Available Methods

The `MockSMTPServer` class provides the following methods:

- `start(timeout=5)` - Start the SMTP server with optional timeout (in seconds)
- `stop(timeout=5)` - Stop the SMTP server with optional timeout (in seconds)
- `reset()` - Clear all stored messages and reset counters
- `get_messages()` - Get a list of all received messages (clears the message queue)
- `get_message_count()` - Get the total count of received messages (doesn't clear the queue)
- `get_results()` - Get a dictionary with server stats and messages
- `is_running()` - Check if the server is currently running

## Message Format

Each message retrieved from `get_messages()` is a dictionary with the following structure:

```python
{
    'peer': (address, port),  # Client connection information
    'mail_from': 'sender@example.com',  # Sender email address
    'rcpt_tos': ['recipient@example.com'],  # List of recipient addresses
    'data': 'Full message content as string'  # The complete email content
}
```

## Thread Safety

The server runs in a separate thread to avoid blocking the main application thread. It handles proper startup and shutdown sequences, including timeouts to prevent hanging.

## Integration with Testing Framework

The mock SMTP server is designed to work with the project's testing framework. It's used in tests to verify that emails are sent correctly during playbook execution. For example, it can validate that:

- Emails are sent to the correct recipients
- Subject and content match expected templates
- Required information is present in the email body
- Attachments are included correctly

When used in automated tests, the server can be reset between test cases to ensure clean testing environments.