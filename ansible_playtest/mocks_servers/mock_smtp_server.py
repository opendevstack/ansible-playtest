#!/usr/bin/env python3
"""
Mock SMTP Server and Manager

This module provides a mock SMTP server for testing email functionality
including server operations, management interface, and command-line capabilities.
Everything integrated in a single file.
"""
import time
import logging  # Needed for log levels
import queue
import signal
import sys
import argparse
import re
from aiosmtpd.controller import Controller

from ansible_playtest.utils.logger import get_logger

# Get a project logger for this module
logger = get_logger(__name__)


class MockSMTPHandler:
    """Handler for the mock SMTP server that stores received messages"""

    def __init__(self):
        """Initialize with empty storage for messages"""
        self.messages = queue.Queue()
        self.received_count = 0

    def extract_subject(self, data):
        """Extract the subject from email data

        Args:
            data (str): The email content

        Returns:
            str: The email subject or '(No subject)' if not found
        """
        # Look for the subject line in the email headers
        subject_match = re.search(r"Subject: (.*?)\r?\n(?!\s)", data, re.DOTALL)
        if subject_match:
            return subject_match.group(1).strip()
        return "(No subject)"

    async def handle_DATA(self, server, session, envelope):
        """Handle the received email data"""
        # Convert data from bytes to string if needed
        data = envelope.content.decode("utf-8", errors="replace")

        # Extract the subject
        subject = self.extract_subject(data)

        # Only log at info level - will be shown only if verbose is enabled
        logger.info(
            f"Received message from {envelope.mail_from} to {envelope.rcpt_tos} - Subject: {subject}"
        )

        # Store the message
        message = {
            "peer": session.peer,
            "mail_from": envelope.mail_from,
            "rcpt_tos": envelope.rcpt_tos,
            "subject": subject,
            "data": data,
        }
        self.messages.put(message)
        self.received_count += 1

        return "250 Message accepted for delivery"


class MockSMTPServer:
    """
    Unified Mock SMTP Server - Combines server, management, and CLI capabilities

    This class provides:
    1. Core SMTP server functionality for testing
    2. Management operations (start, stop, get results)
    3. Command-line interface for standalone operation
    """

    def __init__(self, host="localhost", port=1025, verbose=0):
        """Initialize the server with host and port

        Args:
            host (str): Host to bind the SMTP server to (default: localhost)
            port (int): Port to bind the SMTP server to (default: 1025)
            verbose (bool or int): Enable verbose logging (default: False)
                                  Set to True or 1 for INFO, 2 for DEBUG
        """
        self.host = host
        self.port = port
        self.verbose = verbose
        self.handler = MockSMTPHandler()
        self.controller = None
        self.running = False

        # Set log level based on verbosity
        if verbose:
            if isinstance(verbose, bool) and verbose:
                logger.setLevel(logging.INFO)
            elif verbose >= 2:
                logger.setLevel(logging.DEBUG)
            else:
                logger.setLevel(logging.INFO)

    def start(self, timeout=5):
        """Start the SMTP server in a separate thread

        Args:
            timeout (int): Timeout in seconds to wait for server to start

        Returns:
            self: For method chaining
        """
        if self.running:
            logger.warning("SMTP server is already running")
            return self

        logger.debug(f"Starting mock SMTP server on {self.host}:{self.port}")

        # Create and start SMTP server
        self.controller = Controller(self.handler, hostname=self.host, port=self.port)
        self.controller.start()
        self.running = True

        logger.debug(f"Mock SMTP server started successfully on port {self.port}")

        return self

    def stop(self, timeout=5):
        """Stop the SMTP server

        Args:
            timeout (int): Timeout in seconds to wait for server to stop
        """
        if not self.running:
            logger.debug("SMTP server is not running")
            return

        logger.debug("Stopping mock SMTP server...")

        if self.controller:
            try:
                self.controller.stop()
            except Exception as e:
                logger.error(f"Error closing SMTP server: {str(e)}")

        self.running = False
        logger.debug("Mock SMTP server stopped")

    def reset(self):
        """Reset the message queue"""
        if not self.handler:
            return

        while not self.handler.messages.empty():
            self.handler.messages.get()
        self.handler.received_count = 0
        logger.debug("Mock SMTP server state reset")

    def get_messages(self):
        """Get all received messages

        Returns:
            list: List of message dictionaries
        """
        if not self.handler:
            return []

        messages = []
        while not self.handler.messages.empty():
            messages.append(self.handler.messages.get())
        return messages

    def get_message_count(self):
        """Get the count of received messages

        Returns:
            int: Number of messages received
        """
        if not self.handler:
            return 0
        return self.handler.received_count

    def get_results(self):
        """Get the SMTP server results

        Returns:
            dict: A dictionary containing SMTP server results
        """
        if not self.running:
            return {"error": "SMTP server not running"}

        messages = self.get_messages()
        message_count = self.get_message_count()

        results = {"messages_received": message_count, "messages": messages}

        # Only log summary information if in verbose mode
        if self.verbose:
            logger.info(f"\nSMTP Server Stats:")
            logger.info(f"  Messages received: {results['messages_received']}")

            if message_count > 0 and messages:
                first_msg = messages[0]
                logger.info(f"  First message details:")
                logger.info(f"    From: {first_msg['mail_from']}")
                logger.info(f"    To: {first_msg['rcpt_tos']}")

        return results

    def is_running(self):
        """Check if the SMTP server is running

        Returns:
            bool: True if the server is running, False otherwise
        """
        return self.running

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()

    @classmethod
    def run_command_line(cls):
        """Run the MockSMTPServer from command line"""
        parser = argparse.ArgumentParser(
            description="Run a mock SMTP server for testing"
        )

        parser.add_argument(
            "--host",
            default="localhost",
            help="Hostname to bind the server to (default: localhost)",
        )
        parser.add_argument(
            "--port",
            type=int,
            default=1025,
            help="Port to bind the server to (default: 1025)",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="count",
            default=0,
            help="Enable verbose logging (use -v for INFO level, -vv for DEBUG level)",
        )
        parser.add_argument(
            "--quiet",
            "-q",
            action="store_true",
            help="Suppress all output except critical errors",
        )

        args = parser.parse_args()

        # Configure logging level based on verbosity/quiet settings
        if args.quiet:
            log_level = logging.CRITICAL
        elif args.verbose >= 2:
            log_level = logging.DEBUG
        elif args.verbose == 1:
            log_level = logging.INFO
        else:
            log_level = logging.ERROR

        for handler in logging.root.handlers:
            handler.setLevel(log_level)

        # Create and start the server
        server = cls(
            host=args.host,
            port=args.port,
            verbose=bool(args.verbose),  # Convert count to boolean
        )

        # Handle keyboard interrupt
        def signal_handler(sig, frame):
            if not args.quiet:
                print("\nStopping server...")
                # Print server statistics before stopping
                server_stats = server.get_results()
                print("\nFinal server statistics:")
                print(f"Total messages received: {server_stats['messages_received']}")
            server.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            # Start the server
            server.start()

            # Display server information
            if not args.quiet:
                print(f"Mock SMTP server running on {args.host}:{args.port}")
                print("\nPress Ctrl+C to stop the server")

            while server.running:
                # Print stats periodically only if verbose
                if args.verbose >= 1:
                    messages = server.get_messages()
                    if messages:
                        logger.info(f"\nReceived {len(messages)} new message(s):")
                        for i, msg in enumerate(messages, 1):
                            logger.info(
                                f"  {i}. From: {msg['mail_from']} To: {msg['rcpt_tos']}"
                            )

                time.sleep(2)

        except Exception as e:
            logger.error(f"Error: {e}")
            server.stop()
            sys.exit(1)


# Command-line entry point
def main():
    """Command-line entry point"""
    MockSMTPServer.run_command_line()


if __name__ == "__main__":
    main()
