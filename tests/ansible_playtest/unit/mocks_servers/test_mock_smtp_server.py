#!/usr/bin/env python3
"""
Unit tests for the MockSMTPServer class
"""
import os
import sys
import time
import smtplib
import unittest

from email.message import EmailMessage
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ansible_playtest.mocks_servers.mock_smtp_server import MockSMTPServer, MockSMTPHandler


class TestMockSMTPServer(unittest.TestCase):
    """Test cases for the MockSMTPServer class"""
    
    def setUp(self):
        """Set up the test environment"""
        # Use a different port for tests to avoid conflicts
        self.test_port = 2025
        self.test_host = 'localhost'
        self.server = MockSMTPServer(host=self.test_host, port=self.test_port)
    
    def tearDown(self):
        """Clean up after tests"""
        if self.server.is_running():
            self.server.stop()
    
    def test_server_start_stop(self):
        """Test starting and stopping the server"""
        # Test that server starts properly
        self.server.start()
        self.assertTrue(self.server.is_running())
        
        # Test that server stops properly
        self.server.stop()
        self.assertFalse(self.server.is_running())
    
    def test_server_context_manager(self):
        """Test using the server as a context manager"""
        with MockSMTPServer(host=self.test_host, port=self.test_port) as server:
            self.assertTrue(server.is_running())
        
        # Should be stopped after exiting context
        self.assertFalse(server.is_running())
    
    def test_message_reception(self):
        """Test that the server receives messages correctly"""
        self.server.start()
        
        # Send a test email
        msg = EmailMessage()
        msg['Subject'] = 'Test subject'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg.set_content('This is a test email')
        
        # Connect to the server and send the message
        with smtplib.SMTP(self.test_host, self.test_port) as smtp:
            smtp.send_message(msg)
        
        # Give the server a moment to process
        time.sleep(0.5)
        
        # Check that the message was received
        messages = self.server.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['subject'], 'Test subject')
        self.assertEqual(messages[0]['mail_from'], 'sender@example.com')
        self.assertEqual(messages[0]['rcpt_tos'], ['recipient@example.com'])
        
        # Check message count
        self.assertEqual(self.server.get_message_count(), 1)
    
    def test_reset(self):
        """Test resetting the server state"""
        self.server.start()
        
        # Send a test email
        msg = EmailMessage()
        msg['Subject'] = 'Reset test'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg.set_content('This is a test email for reset')
        
        with smtplib.SMTP(self.test_host, self.test_port) as smtp:
            smtp.send_message(msg)
        
        time.sleep(0.5)
        
        # Verify message was received
        self.assertEqual(self.server.get_message_count(), 1)
        
        # Reset the server
        self.server.reset()
        
        # Check that messages were cleared
        self.assertEqual(self.server.get_message_count(), 0)
        self.assertEqual(len(self.server.get_messages()), 0)
    
    def test_multiple_recipients(self):
        """Test sending to multiple recipients"""
        self.server.start()
        
        # Send a test email with multiple recipients
        msg = EmailMessage()
        msg['Subject'] = 'Multiple recipients'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient1@example.com, recipient2@example.com'
        msg.set_content('This is a test email with multiple recipients')
        
        with smtplib.SMTP(self.test_host, self.test_port) as smtp:
            smtp.send_message(msg)
        
        time.sleep(0.5)
        
        # Check that the message was received with all recipients
        messages = self.server.get_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(len(messages[0]['rcpt_tos']), 2)
        self.assertIn('recipient1@example.com', messages[0]['rcpt_tos'])
        self.assertIn('recipient2@example.com', messages[0]['rcpt_tos'])
    
    def test_get_results(self):
        """Test getting results from the server"""
        self.server.start()
        
        # Send a test email
        msg = EmailMessage()
        msg['Subject'] = 'Results test'
        msg['From'] = 'sender@example.com'
        msg['To'] = 'recipient@example.com'
        msg.set_content('This is a test email for getting results')
        
        with smtplib.SMTP(self.test_host, self.test_port) as smtp:
            smtp.send_message(msg)
        
        time.sleep(0.5)
        
        # Get and check results
        results = self.server.get_results()
        self.assertEqual(results['messages_received'], 1)
        self.assertEqual(len(results['messages']), 1)
        self.assertEqual(results['messages'][0]['subject'], 'Results test')
    

class TestMockSMTPHandler(unittest.TestCase):
    """Test cases for the MockSMTPHandler class"""
    
    def setUp(self):
        """Set up the test environment"""
        self.handler = MockSMTPHandler()
    
    def test_extract_subject_with_subject(self):
        """Test extracting subject when present"""
        email_data = "From: sender@example.com\r\nTo: recipient@example.com\r\nSubject: Test Subject\r\n\r\nBody content"
        subject = self.handler.extract_subject(email_data)
        self.assertEqual(subject, "Test Subject")
    
    def test_extract_subject_without_subject(self):
        """Test extracting subject when not present"""
        email_data = "From: sender@example.com\r\nTo: recipient@example.com\r\n\r\nBody content"
        subject = self.handler.extract_subject(email_data)
        self.assertEqual(subject, "(No subject)")
    
    def test_extract_subject_with_multiline_subject(self):
        """Test extracting a multiline subject"""
        email_data = "From: sender@example.com\r\nTo: recipient@example.com\r\nSubject: Test Subject\r\n With continuation\r\nDate: Thu, 21 Dec 2023 12:00:00 +0000\r\n\r\nBody content"
        subject = self.handler.extract_subject(email_data)
        self.assertEqual(subject, "Test Subject\r\n With continuation")


if __name__ == '__main__':
    unittest.main()
