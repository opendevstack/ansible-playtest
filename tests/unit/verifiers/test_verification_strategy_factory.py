"""
Unit tests for VerificationStrategyFactory in factory.py
"""
import pytest
from ansible_playtest.verifiers.factory import VerificationStrategyFactory
from ansible_playtest.verifiers.module_call import ModuleCallCountVerifier
from ansible_playtest.verifiers.parameter import ParameterValidationVerifier
from ansible_playtest.verifiers.sequence import CallSequenceVerifier
from ansible_playtest.verifiers.error import ErrorVerifier

def test_create_strategies_all():
    scenario_data = {
        'verify': {
            'expected_calls': {'foo': 1},
            'parameter_validation': {'foo': [{'a': 1}]},
            'call_sequence': ['foo'],
            'expected_errors': [{'message': 'fail'}]
        }
    }
    strategies = VerificationStrategyFactory.create_strategies(scenario_data)
    assert any(isinstance(s, ModuleCallCountVerifier) for s in strategies)
    assert any(isinstance(s, ParameterValidationVerifier) for s in strategies)
    assert any(isinstance(s, CallSequenceVerifier) for s in strategies)
    assert any(isinstance(s, ErrorVerifier) for s in strategies)
    assert len(strategies) == 4

def test_create_strategies_some():
    scenario_data = {
        'verify': {
            'expected_calls': {'foo': 1},
            'call_sequence': ['foo']
        }
    }
    strategies = VerificationStrategyFactory.create_strategies(scenario_data)
    assert any(isinstance(s, ModuleCallCountVerifier) for s in strategies)
    assert any(isinstance(s, CallSequenceVerifier) for s in strategies)
    assert not any(isinstance(s, ParameterValidationVerifier) for s in strategies)
    assert not any(isinstance(s, ErrorVerifier) for s in strategies)
    assert len(strategies) == 2

def test_create_strategies_none():
    scenario_data = {'verify': {}}
    strategies = VerificationStrategyFactory.create_strategies(scenario_data)
    assert strategies == []

def test_create_strategies_no_verify():
    scenario_data = {}
    strategies = VerificationStrategyFactory.create_strategies(scenario_data)
    assert strategies == []
