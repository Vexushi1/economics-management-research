"""Phase 3 contracts: synthetic Stackelberg, safe DSL, domains, dimensions."""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from emr.domain.game import (
    GameSpecValidationError,
    MAX_EXPRESSION_DEPTH,
    build_best_response_tasks,
    validate_game_spec,
)

FIXTURES = Path(__file__).resolve().parents[1] / 'fixtures' / 'phase3'


def base():
    return json.loads((FIXTURES / 'stackelberg_synthetic.json').read_text(encoding='utf-8'))


def test_static_stackelberg_structured_model_and_backward_task_order():
    checked = validate_game_spec(base())
    assert checked.classification == 'static_sequential_game'
    assert checked.data['dsl_version'] == '1'
    assert len(checked.data['players']) == 2
    assert len(checked.data['constraints']) == 3
    tasks = build_best_response_tasks(checked)
    assert [(t.player_id, t.stage, t.status) for t in tasks] == [
        ('influencer', 2, 'NOT_SOLVED'), ('retailer', 1, 'NOT_SOLVED')]
    assert 'MATHEMATICAL_VALIDITY_NOT_VERIFIED' in checked.warnings


def test_schema_is_valid_and_mirrored():
    root = Path(__file__).resolve().parents[2]
    schema = json.loads((root / 'schemas/model-spec.schema.json').read_text())
    bundled = (root / 'src/emr/schemas/model-spec.schema.json').read_bytes()
    assert (root / 'schemas/model-spec.schema.json').read_bytes() == bundled
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(base())


@pytest.mark.parametrize('mutation',[
    lambda s: s['players'][0].pop('objective'),
    lambda s: s['symbols'][0].pop('domain'),
    lambda s: s.pop('information_sets'),
    lambda s: s['information_sets'].clear(),
    lambda s: s['symbols'][0]['domain'].update({'lower':'3','upper':'2'}),
    lambda s: s['symbols'][0]['domain'].update({'lower':'0','upper':'0','lower_closed':False}),
    lambda s: s['symbols'][0]['domain'].update({'lower':'nan'}),
    lambda s: s['decisions'][0].update({'symbol':'future_supply'}),
    lambda s: s['players'][1].update({'objective':'e.__class__'}),
    lambda s: s['players'][1].update({'objective': {'op':'call','name':'eval','args':[]}}),
    lambda s: s['players'][1].update({'objective': {'op':'symbol','name':'__import__'}}),
    lambda s: s['players'][1].update({'objective': {'op':'symbol','name':'ghost'}}),
    lambda s: s['players'][1].update({'objective': {'op':'const','value':'1e999999'}}),
    lambda s: s['players'][1].update({'objective': {'op':'pow','base':{'op':'symbol','name':'e'},'exponent':999999999}}),
    lambda s: s.update({'source':{'kind':'paper_anchor','note':'unsourced','page':1,'file_sha256':None}}),
    lambda s: s.update({'time':{'kind':'continuous','stages':2}}),
    lambda s: s['players'][1].update({'objective': {'op':'div','left':{'op':'symbol','name':'e'},'right':{'op':'const','value':'0'}}}),
])
def test_invalid_or_malicious_model_rejected(mutation):
    spec=base()
    mutation(spec)
    with pytest.raises(GameSpecValidationError):
        validate_game_spec(spec)


def test_oversized_model_rejected_early():
    spec=base()
    spec['source']['note']='A'*65536
    with pytest.raises(GameSpecValidationError):
        validate_game_spec(spec)


def test_extreme_nested_ast_rejected_before_schema():
    spec=base()
    node={'op':'symbol','name':'e'}
    for _ in range(MAX_EXPRESSION_DEPTH+3):
        node={'op':'neg','arg':node}
    spec['players'][1]['objective']=node
    with pytest.raises(GameSpecValidationError,match='depth budget'):
        validate_game_spec(spec)


def test_python_payload_is_inert_and_rejected(tmp_path):
    sentinel=tmp_path/'should-not-exist'
    payload=f"__import__('pathlib').Path({str(sentinel)!r}).touch()"
    spec=base()
    spec['players'][1]['objective']=payload
    with pytest.raises(GameSpecValidationError):
        validate_game_spec(spec)
    assert not sentinel.exists()


def test_probability_and_effort_domains_enforced():
    spec=base()
    spec['symbols'][-1]['domain']['lower']=None
    with pytest.raises(GameSpecValidationError,match='nonnegative'):
        validate_game_spec(spec)


def test_dimensional_mismatch_fails():
    spec=base()
    next(s for s in spec['symbols'] if s['name']=='A')['unit']={'quantity':1}
    with pytest.raises(GameSpecValidationError,match='dimensionally inconsistent'):
        validate_game_spec(spec)


def test_original_solver_still_refuses_to_solve():
    from emr.solver.base import ModelSpec, PendingEquilibriumSolver
    s=PendingEquilibriumSolver()
    with pytest.raises(NotImplementedError):
        s.solve(ModelSpec('safe',('retailer','influencer'),('p','e')))


def test_audited_model_data_cannot_be_mutated_externally():
    checked = validate_game_spec(base())
    exposed = checked.data
    exposed['players'][0].pop('objective')
    assert 'objective' in checked.data['players'][0]


def test_information_set_duplicate_observation_rejected():
    spec = base()
    spec['information_sets'][1]['observes'] = ['price_revealed', 'price_revealed']
    with pytest.raises(GameSpecValidationError, match='duplicate observations'):
        validate_game_spec(spec)


def test_unknown_player_information_set_rejected():
    spec = base()
    spec['information_sets'].append({'id':'orphan','player':'ghost','stage':1,'observes':[]})
    with pytest.raises(GameSpecValidationError, match='orphan'):
        validate_game_spec(spec)


def test_viability_constraint_is_explicit_not_assumed():
    item = validate_game_spec(base()).data
    assert any(c["id"] == "viable_market_parameters" and c["relation"] == "gt"
               for c in item["constraints"])


def test_division_by_possibly_zero_parameter_is_blocked():
    spec = base()
    spec['players'][1]['objective'] = {
        'op': 'div', 'left': {'op': 'symbol', 'name': 'e'},
        'right': {'op': 'symbol', 'name': 'w'},
    }
    with pytest.raises(GameSpecValidationError, match='potential zero denominator'):
        validate_game_spec(spec)


def test_division_by_strictly_positive_parameter_is_permitted_as_structure():
    spec = base()
    spec['players'][1]['objective'] = {
        'op': 'div', 'left': {'op': 'symbol', 'name': 'e'},
        'right': {'op': 'symbol', 'name': 'c'},
    }
    assert validate_game_spec(spec).classification == 'static_sequential_game'
