import pytest

from kvadapt.workload_audit import audit_workload
from kvadapt.workloads import build_workload

@pytest.mark.parametrize(
    ('fraction', 'unique_prefixes', 'repeated_occurrences'),
    [(0.0, 60, 0), (0.5, 34, 26), (1.0, 4, 56)],
)
def test_prefix_counts(fraction, unique_prefixes, repeated_occurrences):
    requests = build_workload(60, fraction)
    result = audit_workload(requests)
    assert result['unique_prefixes'] == unique_prefixes
    assert result['repeat_occurrences_after_first'] == repeated_occurrences

def test_duplicate_request_id():
    requests = build_workload(4, 0.0)
    requests[1]['request_id'] = requests[0]['request_id']
    with pytest.raises(ValueError, match='unique integer'):
        audit_workload(requests)

def test_inconsistent_prefix_group():
    requests = build_workload(8, 1.0, prefix_groups=2)
    group = requests[0]['prefix_group']
    requests[0]['prompt'] = 'Different prefix\nQuestion 0: Explain caching.'
    assert sum(r['prefix_group'] == group for r in requests) > 1
    with pytest.raises(ValueError, match='different prefixes'):
        audit_workload(requests)
