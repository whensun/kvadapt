
import json
from pathlib import Path

from kvadapt.benchmark import load_workload, run_benchmark

def main() -> None:
    model = 'Qwen/Qwen3-0.6B'
    base_url = 'http://127.0.0.1:8000'
    scenarios = ['no_reuse', 'mixed_reuse', 'high_reuse']
    concurrencies = [1, 4]
    output_dir = Path('results/benchmarks')
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        requests = load_workload(Path('results/workloads') / f'{scenario}.jsonl')
        for concurrency in concurrencies:
            summary = run_benchmark(requests, base_url, model, concurrency)
            path = output_dir / f'{scenario}_c{concurrency}.json'
            path.write_text(json.dumps(summary, indent=2), encoding='utf-8')
            print(f'{scenario} | concurrency={concurrency}')
            print(f'Throughput: {summary["output_tokens_per_second"]:.2f} tokens/sec')
            print(f'Mean TTFT: {summary["mean_ttft_ms"]}')
            print(f'Mean TPOT: {summary["mean_tpot_ms"]}')
            print(f'Results: {path}')

if __name__ == '__main__':
    main()
