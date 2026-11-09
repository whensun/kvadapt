import subprocess
import sys
from pathlib import Path

RUNNER = Path(__file__).resolve().parents[1] / 'benchmarks' / 'run_benchmark.py'

def run_cli(tmp_path: Path, *options: str) -> subprocess.CompletedProcess:
    (tmp_path / 'no_reuse.jsonl').write_text('{"request_id": 0, "prompt": "hello", "max_tokens": 3}\n', encoding='utf-8')
    return subprocess.run([sys.executable, str(RUNNER), '--scenarios', 'no_reuse', '--workload-dir', str(tmp_path), '--dry-run', *options], capture_output=True, text=True, check=False)

def test_runner_dry_run(tmp_path):
    result = run_cli(tmp_path, '--label', 'mock', '--concurrencies', '1', '4')
    assert result.returncode == 0
    assert 'concurrency=1' in result.stdout
    assert 'concurrency=4' in result.stdout

def test_runner_invalid_concurrency(tmp_path):
    result = run_cli(tmp_path, '--label', 'mock', '--concurrencies', '0')
    assert result.returncode != 0
    assert 'must be positive' in result.stderr

def test_runner_invalid_label(tmp_path):
    result = run_cli(tmp_path, '--label', '../mock')
    assert result.returncode != 0
    assert 'label must contain' in result.stderr

def test_runner_invalid_repeats(tmp_path):
    result = run_cli(tmp_path, '--label', 'mock', '--repeats', '0')
    assert result.returncode != 0
    assert 'must be positive' in result.stderr
