"""
Unit tests for ErrorVerifier in error.py
"""
import pytest
from ansible_playtest.verifiers.error import ErrorVerifier

def test_error_verifier_pass():
    verifier = ErrorVerifier()
    scenario_data = {
        'verify': {
            'expected_errors': [
                {'message': 'fail', 'task': 'foo'}
            ]
        }
    }
    playbook_stats = {
        'errors': [
            {'message': 'fail: something bad', 'task': 'foo'}
        ],
        'play_recap': {'hosts': {'host1': {'failures': 0}}}
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert result['error_checks'][0]['found']
    assert result['process_failure']['passed']
    assert verifier.get_status() is True

def test_error_verifier_fail_missing_error():
    verifier = ErrorVerifier()
    scenario_data = {
        'verify': {
            'expected_errors': [
                {'message': 'fail', 'task': 'foo'}
            ]
        }
    }
    playbook_stats = {
        'errors': [
            {'message': 'other error', 'task': 'foo'}
        ],
        'play_recap': {'hosts': {'host1': {'failures': 0}}}
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert not result['error_checks'][0]['found']
    assert result['process_failure']['passed']
    assert verifier.get_status() is False

def test_error_verifier_process_failure_expected_and_actual():
    verifier = ErrorVerifier()
    scenario_data = {
        'verify': {
            'expected_errors': [
                {'message': 'fail', 'task': 'foo', 'expect_process_failure': True}
            ]
        }
    }
    playbook_stats = {
        'errors': [
            {'message': 'fail: something bad', 'task': 'foo'}
        ],
        'play_recap': {'hosts': {'host1': {'failures': 1}}}
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['process_failure']['expected'] is True
    assert result['process_failure']['actual'] is True
    assert result['process_failure']['passed'] is True
    assert result['_overall_pass']
    assert verifier.get_status() is True

def test_error_verifier_process_failure_expected_but_not_actual():
    verifier = ErrorVerifier()
    scenario_data = {
        'verify': {
            'expected_errors': [
                {'message': 'fail', 'task': 'foo', 'expect_process_failure': True}
            ]
        }
    }
    playbook_stats = {
        'errors': [
            {'message': 'fail: something bad', 'task': 'foo'}
        ],
        'play_recap': {'hosts': {'host1': {'failures': 0}}}
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['process_failure']['expected'] is True
    assert result['process_failure']['actual'] is False
    assert not result['process_failure']['passed']
    assert not result['_overall_pass']
    assert verifier.get_status() is False

def test_error_verifier_no_expected_errors():
    verifier = ErrorVerifier()
    scenario_data = {'verify': {}}
    playbook_stats = {}
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert verifier.get_status() is True
