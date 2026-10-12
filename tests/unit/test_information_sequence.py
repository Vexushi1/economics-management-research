"""Explicit information sets prohibit observing future state or actions."""

import copy
import json
from pathlib import Path

import pytest

from emr.domain.game import GameSpecValidationError, validate_game_spec

F = Path(__file__).resolve().parents[1] / 'fixtures' / 'phase3'


def omega():
    return json.loads((F / 'omega_supply_taxonomy.json').read_text())


def test_omega_random_supply_structural_classification_not_hjb():
    """Illustrative taxonomy, not a verified extraction of original author equations."""
    model = validate_game_spec(omega())
    assert model.classification == 'stochastic_sequential_game'
    assert model.data['time']['kind']=='discrete'
    assert 'STOCHASTIC_DISTRIBUTION_UNSPECIFIED' in model.warnings


def test_future_supply_knowledge_is_rejected():
    spec=omega()
    spec['information_sets'][0]['observes']=['supply_public']
    with pytest.raises(GameSpecValidationError,match='future'):
        validate_game_spec(spec)


def test_early_actor_cannot_see_later_decision():
    spec=omega()
    spec['signals'].append({'id':'effort_signal','kind':'decision','decision_id':'effort_choice','available_stage':3})
    spec['information_sets'][0]['observes']=['effort_signal']
    with pytest.raises(GameSpecValidationError,match='future'):
        validate_game_spec(spec)


def test_same_stage_decision_signal_disallowed():
    spec=omega()
    spec['signals'][0]['available_stage']=1
    with pytest.raises(GameSpecValidationError,match='own stage'):
        validate_game_spec(spec)


def test_unknown_signal_rejected():
    spec=omega()
    spec['information_sets'][1]['observes']=['unknown_signal']
    with pytest.raises(GameSpecValidationError,match='unknown signal'):
        validate_game_spec(spec)


def test_wrong_info_owner_or_stage_rejected():
    for field,value in [('player','platform'),('stage',1)]:
        spec=omega()
        spec['information_sets'][1][field]=value
        with pytest.raises(GameSpecValidationError,match='owner or stage'):
            validate_game_spec(spec)


def test_missing_information_set_reference_rejected():
    spec=omega()
    spec['decisions'][0]['information_set']='missing'
    with pytest.raises(GameSpecValidationError,match='missing decision information'):
        validate_game_spec(spec)


def test_probability_bounds_and_zero_one_states():
    spec=omega()
    sym=next(x for x in spec['symbols'] if x['name']=='supply')
    assert validate_game_spec(spec).classification == 'stochastic_sequential_game'
    sym['domain']['upper']='2'
    with pytest.raises(GameSpecValidationError,match='probability'):
        validate_game_spec(spec)


def test_random_state_without_distribution_cannot_claim_verified():
    spec=omega()
    sym=next(x for x in spec['symbols'] if x['name']=='supply')
    sym['distribution_status']='NOT_APPLICABLE'
    with pytest.raises(GameSpecValidationError,match='stochastic'):
        validate_game_spec(spec)


def test_case_does_not_modify_original_fixture():
    assert omega()==copy.deepcopy(omega())
