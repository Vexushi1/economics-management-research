# Phase 6 conservative replication example

This demonstration uses **entirely synthetic** source identities and numbers. It does not claim to reproduce any published journal article. No real PDF is distributed.

The required input records a paper SHA-256, source anchors for the model formulas and each target, and every required parameter with an explicitly supplied value and source reference. A missing parameter/variance/cost coefficient yields `UNREPRODUCIBLE_INPUT` before numerical evaluation. A separate comparison can report `NUMERIC_MATCH` or `NUMERIC_MISMATCH` only for declared target values, not for the complete article.

```python
from emr.domain.replication import build_replication_manifest

request = {
    "paper_sha256": "a" * 64, "model_id": "synthetic_demo",
    "required_parameters": ["unit_cost", "supply_variance"],
    "parameters": {"unit_cost": {"value": "2", "source_ref": "synthetic:2"}},
    "formula_anchors": ["synthetic:equation1"],
    "targets": [{"id": "figure1", "kind": "FIGURE", "source_ref": "synthetic:figure1"}],
}
report = build_replication_manifest(request)
assert report["status"] == "UNREPRODUCIBLE_INPUT"
assert report["missing_requirements"] == ["supply_variance"]
```

Dynamic models and random-supply settings from published papers must be populated from the actual sources; no model parameters have been harvested or published in this example.
