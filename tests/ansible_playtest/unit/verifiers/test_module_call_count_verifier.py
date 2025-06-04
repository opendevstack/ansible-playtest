"""
Unit tests for ModuleCallCountVerifier in module_call.py
"""
import pytest
from ansible_playtest.verifiers.module_call import ModuleCallCountVerifier

def test_module_call_count_verifier_pass():
    verifier = ModuleCallCountVerifier()
    scenario_data = {
        'verify': {
            'expected_calls': {
                'foo': 2,
                'bar': 1
            }
        }
    }
    playbook_stats = {
        'module_calls': {
            'foo': 2,
            'bar': 1
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert result['foo']['passed']
    assert result['bar']['passed']
    assert verifier.get_status() is True

def test_module_call_count_verifier_fail():
    verifier = ModuleCallCountVerifier()
    scenario_data = {
        'verify': {
            'expected_calls': {
                'foo': 2,
                'bar': 1
            }
        }
    }
    playbook_stats = {
        'module_calls': {
            'foo': 1,
            'bar': 0
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert not result['foo']['passed']
    assert not result['bar']['passed']
    assert verifier.get_status() is False

def test_module_call_count_verifier_no_config():
    verifier = ModuleCallCountVerifier()
    scenario_data = {'verify': {}}
    playbook_stats = {}
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert verifier.get_status() is True
