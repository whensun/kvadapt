
import json
from pathlib import Path

from kvadapt.analysis import load_runs, summarize_runs

def make_run(throughput: float, label: str = 'mock', session: str = 'mock_session') -> dict:
    return {
        'session': session,
        'label': label,
        'model': 'test-model',
        'scenario': 'high_reuse',
        'metrics': {
            'concurrency': 4,
            'output_tokens_per_second': throughput,
            'mean_ttft_ms': 20.0,
            'mean_tpot_ms': 10.0,
            'mean_chunk_itl_ms': 8.0,
        },
    }

def test_summary_aggregates_repeats():
    rows = summarize_runs([make_run(100.0), make_run(120.0)])
    assert len(rows) == 1
    assert rows[0]['runs'] == 2
    assert rows[0]['throughput_mean'] == 110.0
    assert round(rows[0]['throughput_stdev'], 3) == 14.142
    assert rows[0]['ttft_mean_ms'] == 20.0

def test_summary_separates_sessions():
    rows = summarize_runs([make_run(100.0), make_run(120.0, session='other_session')])
    assert len(rows) == 2
    assert all(row['throughput_stdev'] is None for row in rows)

def test_load_runs_filters_label(tmp_path: Path):
    folder = tmp_path / 'mock_session'
    folder.mkdir()
    (folder / 'high_reuse_c4_r01.json').write_text(json.dumps(make_run(100.0)), encoding='utf-8')
    (folder / 'high_reuse_c4_r02.json').write_text(json.dumps(make_run(120.0, 'baseline')), encoding='utf-8')
    assert len(load_runs(tmp_path, 'mock')) == 1
    assert len(load_runs(tmp_path)) == 2
