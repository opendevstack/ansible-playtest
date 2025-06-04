"""
Unit tests for ParameterValidationVerifier in parameter.py
"""
import pytest
from ansible_playtest.verifiers.parameter import ParameterValidationVerifier

def test_parameter_validation_verifier_pass():
    verifier = ParameterValidationVerifier()
    scenario_data = {
        'verify': {
            'parameter_validation': {
                'my_module': [
                    {'param1': 'a', 'param2': 2}
                ]
            }
        }
    }
    playbook_stats = {
        'call_details': {
            'my_module': [
                {'params': {'param1': 'a', 'param2': 2}}
            ]
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert result['my_module']['passed']
    assert verifier.get_status() is True

def test_parameter_validation_verifier_fail_wrong_value():
    verifier = ParameterValidationVerifier()
    scenario_data = {
        'verify': {
            'parameter_validation': {
                'my_module': [
                    {'param1': 'a', 'param2': 2}
                ]
            }
        }
    }
    playbook_stats = {
        'call_details': {
            'my_module': [
                {'params': {'param1': 'a', 'param2': 3}}
            ]
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert not result['my_module']['passed']
    assert verifier.get_status() is False
    assert result['my_module']['details'][0]['status'] == 'failed'
    assert result['my_module']['details'][0]['failures'][0]['param'] == 'param2'

def test_parameter_validation_verifier_fail_missing_param():
    verifier = ParameterValidationVerifier()
    scenario_data = {
        'verify': {
            'parameter_validation': {
                'my_module': [
                    {'param1': 'a', 'param2': 2}
                ]
            }
        }
    }
    playbook_stats = {
        'call_details': {
            'my_module': [
                {'params': {'param1': 'a'}}
            ]
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert not result['my_module']['passed']
    assert verifier.get_status() is False
    assert result['my_module']['details'][0]['status'] == 'failed'
    assert result['my_module']['details'][0]['failures'][0]['param'] == 'param2'

def test_parameter_validation_verifier_missing_call():
    verifier = ParameterValidationVerifier()
    scenario_data = {
        'verify': {
            'parameter_validation': {
                'my_module': [
                    {'param1': 'a', 'param2': 2},
                    {'param1': 'b', 'param2': 3}
                ]
            }
        }
    }
    playbook_stats = {
        'call_details': {
            'my_module': [
                {'params': {'param1': 'a', 'param2': 2}}
            ]
        }
    }
    result = verifier.verify(scenario_data, playbook_stats)
    assert not result['_overall_pass']
    assert not result['my_module']['passed']
    assert result['my_module']['details'][1]['status'] == 'missing'

def test_parameter_validation_verifier_no_config():
    verifier = ParameterValidationVerifier()
    scenario_data = {}
    playbook_stats = {}
    result = verifier.verify(scenario_data, playbook_stats)
    assert result['_overall_pass']
    assert verifier.get_status() is True
