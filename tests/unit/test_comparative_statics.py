"""Never announce a sign from a few numerical samples."""

import sympy as sp

from emr.adapters.symbolic_sympy import compare_statics


def test_constant_derivative_sign_is_exact_and_domain_is_explicit():
    x = sp.Symbol("x", real=True)
    result = compare_statics(-2*x, x)
    assert result["status"] == "NEGATIVE"
    assert "domain" in result


def test_undetermined_sign_not_fabricated():
    x = sp.Symbol("x", real=True)
    result = compare_statics(x*x, x)
    assert result["status"] == "SIGN_INDETERMINATE"
    assert result["proof"] == "NOT_VERIFIED"
