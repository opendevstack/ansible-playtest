"""
Unit tests for CallSequenceVerifier in sequence.py
"""
import pytest
from ansible_playtest.verifiers.sequence import CallSequenceVerifier

def test_call_sequence_verifier_pass():
    verifier = CallSequenceVerifier()
    scenario_data = {
        'verify': {
            'call_sequence': ['a', 'b', 'c']
        }
    }
    playbook_stats = {
        'call_sequence': ['x', 'a', 'y', 'b', 'z', 'c']
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert verifier.get_status() is True
    assert result['errors'] == []

def test_call_sequence_verifier_fail():
    verifier = CallSequenceVerifier()
    scenario_data = {
        'verify': {
            'call_sequence': ['a', 'b', 'c']
        }
    }
    playbook_stats = {
        'call_sequence': ['a', 'x', 'z', 'c']
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert verifier.get_status() is False
    assert 'Missing expected module: b' in result['errors'][0]

def test_call_sequence_verifier_no_config():
    verifier = CallSequenceVerifier()
    scenario_data = {}
    playbook_stats = {}
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert verifier.get_status() is True
