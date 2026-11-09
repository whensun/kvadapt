
import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from kvadapt.benchmark import load_workload, run_benchmark

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run KVAdapt serving benchmarks')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--model', default='Qwen/Qwen3-0.6B')
    parser.add_argument('--label', required=True)
    parser.add_argument('--scenarios', nargs='+', choices=['no_reuse', 'mixed_reuse', 'high_reuse'], default=['no_reuse', 'mixed_reuse', 'high_reuse'])
    parser.add_argument('--concurrencies', nargs='+', type=int, default=[1, 4])
    parser.add_argument('--repeats', type=int, default=1)
    parser.add_argument('--workload-dir', type=Path, default=Path('results/workloads'))
    parser.add_argument('--output-dir', type=Path, default=Path('results/benchmarks'))
    parser.add_argument('--dry-run', action='store_true')
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_-]+', args.label):
        raise ValueError('label must contain only letters, numbers, underscore, or hyphen')
    if args.repeats < 1 or any(value < 1 for value in args.concurrencies):
        raise ValueError('repeats and concurrencies must be positive')
    workloads = {}
    for scenario in args.scenarios:
        path = args.workload_dir / f'{scenario}.jsonl'
        requests = load_workload(path)
        if not requests:
            raise ValueError(f'Empty workload: {path}')
        workloads[scenario] = (path, requests)
    if args.dry_run:
        for scenario in args.scenarios:
            for concurrency in args.concurrencies:
                print(f'{scenario}: {len(workloads[scenario][1])} requests, concurrency={concurrency}, repeats={args.repeats}')
        return
    session = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    session_dir = args.output_dir / f'{args.label}_{session}'
    session_dir.mkdir(parents=True, exist_ok=False)
    for scenario in args.scenarios:
        workload_path, requests = workloads[scenario]
        for concurrency in args.concurrencies:
            for repeat in range(1, args.repeats + 1):
                summary = run_benchmark(requests, args.base_url, args.model, concurrency)
                record = {
                    'label': args.label,
                    'created_at_utc': datetime.now(timezone.utc).isoformat(),
                    'scenario': scenario,
                    'repeat': repeat,
                    'base_url': args.base_url,
                    'model': args.model,
                    'workload_file': str(workload_path),
                    'metrics': summary,
                }
                path = session_dir / f'{scenario}_c{concurrency}_r{repeat:02d}.json'
                path.write_text(json.dumps(record, indent=2), encoding='utf-8')
                print(f'{scenario} | c={concurrency} | run={repeat} | throughput={summary["output_tokens_per_second"]:.2f} tokens/sec')
                print(f'Result: {path}')

if __name__ == '__main__':
    main()
