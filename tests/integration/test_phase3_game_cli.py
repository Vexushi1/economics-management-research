"""Strictly offline JSON game validation and no-execution CLI behavior."""

import json
from pathlib import Path

from emr.cli import main

F = Path(__file__).resolve().parents[1] / 'fixtures' / 'phase3'


def test_cli_phase3_validates_synthetic_without_solving(capsys):
    assert main(['model','validate',str(F/'stackelberg_synthetic.json')]) == 0
    result=json.loads(capsys.readouterr().out)
    assert result['classification']=='static_sequential_game'
    assert result['status']=='STRUCTURALLY_VALID_NOT_SOLVED'
    assert main(['model','tasks',str(F/'stackelberg_synthetic.json')]) == 0
    tasks=json.loads(capsys.readouterr().out)['tasks']
    assert [t['control_symbol'] for t in tasks]==['e','p']
    assert all(t['status']=='NOT_SOLVED' for t in tasks)


def test_cli_rejects_bad_or_duplicate_json(tmp_path,capsys):
    for text in ['{"model_id":"x","model_id":"x"}', '__import__("os")', '{"bad": NaN}']:
        f=tmp_path/'bad.json'
        f.write_text(text)
        assert main(['model','validate',str(f)])==2
        assert not capsys.readouterr().out


def test_cli_rejects_oversize_input_without_loading(tmp_path,capsys):
    f=tmp_path/'huge.json'
    f.write_bytes(b'{"x":"'+b'x'*65540+b'"}')
    assert main(['model','validate',str(f)])==2
    assert not capsys.readouterr().out


def test_cli_rejects_symlink(tmp_path,capsys):
    shortcut=tmp_path/'link.json'
    shortcut.symlink_to(F/'stackelberg_synthetic.json')
    assert main(['model','validate',str(shortcut)])==2
    assert not capsys.readouterr().out
