import json
import math
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx

@dataclass
class RequestMetrics:
    request_id: int
    output_tokens: int
    elapsed_seconds: float
    ttft_ms: float | None
    tpot_ms: float | None
    chunk_itl_ms: float | None

def load_workload(path: Path) -> list[dict]:
    with path.open(encoding='utf-8') as file:
        return [json.loads(line) for line in file if line.strip()]

def percentile(values: list[float], percent: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(len(ordered) * percent / 100) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]

def measure_request(client: httpx.Client, url: str, model: str, request: dict) -> RequestMetrics:
    payload = {
        'model': model,
        'prompt': request['prompt'],
        'max_tokens': request['max_tokens'],
        'temperature': 0,
        'stream': True,
        'stream_options': {'include_usage': True},
    }
    start = time.perf_counter()
    first = None
    previous = None
    gaps = []
    output_tokens = None
    with client.stream('POST', url, json=payload) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line.startswith('data:'):
                continue
            data = line[5:].strip()
            if data == '[DONE]':
                break
            chunk = json.loads(data)
            if chunk.get('error'):
                raise ValueError(f'Server error: {chunk["error"]}')
            usage = chunk.get('usage')
            if usage is not None:
                output_tokens = usage.get('completion_tokens')
            choices = chunk.get('choices') or []
            if choices and choices[0].get('text'):
                now = time.perf_counter()
                if first is None:
                    first = now
                if previous is not None:
                    gaps.append((now - previous) * 1000)
                previous = now
    end = time.perf_counter()
    if not isinstance(output_tokens, int) or output_tokens < 0:
        raise ValueError('Streaming response is missing valid completion_tokens usage')
    if output_tokens > 0 and first is None:
        raise ValueError('Streaming response has tokens but no text chunks')
    ttft_ms = (first - start) * 1000 if first is not None else None
    tpot_ms = (end - first) * 1000 / (output_tokens - 1) if first is not None and output_tokens > 1 else None
    chunk_itl_ms = statistics.mean(gaps) if gaps else None
    return RequestMetrics(request['request_id'], output_tokens, end - start, ttft_ms, tpot_ms, chunk_itl_ms)

def run_benchmark(requests: list[dict], base_url: str, model: str, concurrency: int, transport: httpx.BaseTransport | None = None) -> dict:
    if not requests or concurrency < 1:
        raise ValueError('requests must be nonempty and concurrency must be positive')
    url = f'{base_url.rstrip("/")}/v1/completions'
    with httpx.Client(timeout=180, limits=httpx.Limits(max_connections=concurrency), transport=transport) as client:
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            results = list(executor.map(lambda request: measure_request(client, url, model, request), requests))
        duration = time.perf_counter() - start
    output_tokens = sum(result.output_tokens for result in results)
    ttfts = [result.ttft_ms for result in results if result.ttft_ms is not None]
    tpots = [result.tpot_ms for result in results if result.tpot_ms is not None]
    chunk_itls = [result.chunk_itl_ms for result in results if result.chunk_itl_ms is not None]
    return {
        'model': model,
        'concurrency': concurrency,
        'requests': len(requests),
        'duration_seconds': duration,
        'output_tokens': output_tokens,
        'output_tokens_per_second': output_tokens / duration,
        'requests_per_second': len(requests) / duration,
        'mean_ttft_ms': statistics.mean(ttfts) if ttfts else None,
        'p99_ttft_ms': percentile(ttfts, 99),
        'mean_tpot_ms': statistics.mean(tpots) if tpots else None,
        'p99_tpot_ms': percentile(tpots, 99),
        'mean_chunk_itl_ms': statistics.mean(chunk_itls) if chunk_itls else None,
        'results': [asdict(result) for result in results],
    }
