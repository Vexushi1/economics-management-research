"""Phase 9 incremental invalidation with no prior literature redo."""

import pytest

from emr.core.cache import CacheIntegrityError, ExecutionCache, fingerprint


def test_only_derived_tasks_stale_after_model_version_change():
    cache = ExecutionCache()
    pdf = fingerprint({'page': 1, 'quote': 'original synthetic source'})
    model = fingerprint({'gamma': '0.2'})
    new_model = fingerprint({'gamma': '0.3'})
    cache.put('literature', 'v1', {'source_status': 'NOT_VERIFIED'}, {'pdf': pdf})
    cache.put('solver', 'v1', {'result': 'checked'}, {'model': model})
    cache.put('manuscript', 'v1', {'proof': 'not_auto_certified'}, {'model': model})
    assert cache.get('literature', 'v1', {'pdf': pdf})[0] == 'HIT'
    assert cache.get('solver', 'v1', {'model': new_model})[0] == 'STALE'
    assert cache.get('manuscript', 'v1', {'model': new_model})[0] == 'STALE'
    assert cache.get('literature', 'v1', {'pdf': pdf})[0] == 'HIT'
    assert cache.get('solver', 'v2', {'model': model})[0] == 'STALE'


def test_non_json_cache_object_rejected_without_pickling():
    cache = ExecutionCache()
    with pytest.raises(CacheIntegrityError):
        cache.put('x', 'v1', {'unsafe': object()}, {'pdf': '0' * 64})
