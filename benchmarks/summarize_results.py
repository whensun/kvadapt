import argparse
import csv
from pathlib import Path

from kvadapt.analysis import load_runs, summarize_runs

def main() -> None:
    parser = argparse.ArgumentParser(description='Summarize KVAdapt benchmark results')
    parser.add_argument('--root', type=Path, default=Path('results/benchmarks'))
    parser.add_argument('--label')
    args = parser.parse_args()
    runs = load_runs(args.root, args.label)
    if not runs:
        raise SystemExit('No benchmark runs found')
    rows = summarize_runs(runs)
    path = args.root / ('summary.csv' if args.label is None else f'summary_{args.label}.csv')
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        spread = 'n/a' if row['throughput_stdev'] is None else f'{row["throughput_stdev"]:.2f}'
        print(f'{row["session"]} | {row["scenario"]} | c={row["concurrency"]} | n={row["runs"]} | throughput={row["throughput_mean"]:.2f} +/- {spread} tok/s')
    print(f'Saved: {path}')

if __name__ == '__main__':
    main()
