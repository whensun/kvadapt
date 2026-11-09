import json
import statistics
from collections import defaultdict
from pathlib import Path

def load_runs(root: Path, label: str | None = None) -> list[dict]:
    runs = []
    for path in sorted(root.rglob('*_c*_r*.json')):
        record = json.loads(path.read_text(encoding='utf-8'))
        if label is None or record['label'] == label:
            record['session'] = path.parent.name
            runs.append(record)
    return runs

def metric_mean(runs: list[dict], name: str) -> float | None:
    values = [run['metrics'][name] for run in runs if run['metrics'].get(name) is not None]
    return statistics.mean(values) if values else None

def summarize_runs(runs: list[dict]) -> list[dict]:
    groups = defaultdict(list)
    for run in runs:
        key = (run['session'], run['label'], run['model'], run['scenario'], run['metrics']['concurrency'])
        groups[key].append(run)
    rows = []
    for (session, label, model, scenario, concurrency), group in sorted(groups.items()):
        throughputs = [run['metrics']['output_tokens_per_second'] for run in group]
        rows.append({
            'session': session,
            'label': label,
            'model': model,
            'scenario': scenario,
            'concurrency': concurrency,
            'runs': len(group),
            'throughput_mean': statistics.mean(throughputs),
            'throughput_stdev': statistics.stdev(throughputs) if len(throughputs) > 1 else None,
            'ttft_mean_ms': metric_mean(group, 'mean_ttft_ms'),
            'tpot_mean_ms': metric_mean(group, 'mean_tpot_ms'),
            'chunk_itl_mean_ms': metric_mean(group, 'mean_chunk_itl_ms'),
        })
    return rows
