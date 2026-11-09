
import pytest
from kvadapt.workloads import build_workload, write_workload

def test_deterministic():
    a = build_workload(20, 0.5, seed=42)
    b = build_workload(20, 0.5, seed=42)
    assert a == b

def test_shared_prefixes():
    requests = build_workload(12, 1.0, prefix_groups=3)
    assert len({r['prefix_group'] for r in requests}) == 3
    assert len({r['prompt'].split('\n')[0] for r in requests}) == 3

def test_no_reuse():
    requests = build_workload(12, 0.0)
    assert all(r['prefix_group'] is None for r in requests)
    assert len({r['prompt'].split('\n')[0] for r in requests}) == 12

def test_invalid_fraction():
    with pytest.raises(ValueError):
        build_workload(10, 1.5)

def test_write_workload(tmp_path):
    requests = build_workload(5, 0.5)
    path = tmp_path / 'workload.jsonl'
    write_workload(path, requests)
    assert len(path.read_text().splitlines()) == 5
