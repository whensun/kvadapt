
from pathlib import Path

from kvadapt.benchmark import load_workload
from kvadapt.workload_audit import audit_workload

def main() -> None:
    root = Path('results/workloads')
    for name in ['no_reuse', 'mixed_reuse', 'high_reuse']:
        requests = load_workload(root / f'{name}.jsonl')
        result = audit_workload(requests)
        print(f'\n{name}')
        for key, value in result.items():
            print(f'{key}: {value}')

if __name__ == '__main__':
    main()
