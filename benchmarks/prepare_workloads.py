
from pathlib import Path
from kvadapt.workloads import build_workload, write_workload

def main() -> None:
    scenarios = {'no_reuse': 0.0, 'mixed_reuse': 0.5, 'high_reuse': 1.0}
    for name, fraction in scenarios.items():
        requests = build_workload(count=60, shared_fraction=fraction)
        path = Path('results/workloads') / f'{name}.jsonl'
        write_workload(path, requests)
        print(f'{name}: {len(requests)} requests -> {path}')

if __name__ == '__main__':
    main()
