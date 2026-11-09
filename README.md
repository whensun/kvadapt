# KVAdapt

**KV-Cache-Aware Request Admission for vLLM**

KVAdapt is a custom vLLM scheduler that explores request admission under limited key-value (KV) cache capacity.

It reduces the time to first token (TTFT) for shorter requests by allowing them to bypass larger waiting requests when sufficient KV-cache blocks are available. To limit unfairness, KVAdapt restricts how often a waiting request can be bypassed.

## Motivation

Large language model (LLM) serving systems process requests with different prompt lengths and memory requirements.

When the KV-cache is nearly full, a waiting request may require more memory than is currently available. Smaller requests behind it may be able to run, but first-come-first-served (FCFS) admission can delay them.

KVAdapt investigates whether bounded request reordering can reduce this delay without substantially affecting overall throughput.

## Implementation

KVAdapt extends the vLLM v1 scheduler with KV-cache-aware admission reordering.

Before scheduling, it:

1. Checks whether the first waiting request fits in the available KV-cache.
2. Inspects up to four waiting requests when the first request does not fit.
3. Selects the smallest eligible request that fits.
4. Moves the selected request to the front of the waiting queue.
5. Limits the number of times the original request can be bypassed.

The selected configuration allows **one bypass per waiting request**.

KVAdapt supports vLLM asynchronous scheduling and uses the existing vLLM execution engine.

The repository also includes experimental First-Fit, Two-Bypasses, and No-Op scheduler variants.

## Requirements

- Python 3.12 or newer
- vLLM 0.33.0
- A CUDA-capable GPU supported by vLLM
- `uv` for managing the project environment

The scheduler uses internal vLLM interfaces, so compatibility with other vLLM versions is not guaranteed.

The benchmark configuration uses a 2 GiB GPU KV-cache allocation. This is an experimental constraint, not a recommended production setting.

## Installation and Testing

Install the project dependencies:

```bash
uv sync
```

Run the test suite:

```bash
uv run pytest -q
```

The validated test suite contains 30 test cases covering admission selection, workload generation, benchmarking, metrics, and result analysis.

Install vLLM 0.33.0 in a separate compatible environment following the official vLLM installation instructions.

## Running KVAdapt

From the repository root:

```bash
PYTHONPATH="$PWD/src" "$HOME/.venvs/kvadapt-vllm/bin/vllm" serve Qwen/Qwen3-0.6B \
    --host 127.0.0.1 \
    --port 8000 \
    --max-model-len 4096 \
    --kv-cache-memory-bytes 2G \
    --enable-prefix-caching \
    --watermark 0.05 \
    --async-scheduling \
    --scheduler-cls kvadapt.scheduler_async_one_bypass.KVAdaptAsyncOneBypassScheduler
```

Replace the vLLM executable path if your environment is different.

To run the original vLLM asynchronous scheduler, restart the server with the same configuration but omit `--scheduler-cls`.

## Benchmark

The main evaluation uses:

| Parameter | Configuration |
|---|---|
| Model | Qwen/Qwen3-0.6B |
| vLLM | 0.33.0 |
| KV-cache allocation | 2 GiB |
| Maximum model length | 4,096 tokens |
| Maximum request concurrency | 16 |
| Requests per seed | 160 |
| Seeds | 0-4 |
| Dataset | Random |
| Input length | 409-3,687 tokens |
| Output length | 25-231 tokens |
| Sampling temperature | 0 |
| Early EOS termination | Disabled |

Each scheduler processes 800 requests across five seeds.

To reproduce a benchmark, start the desired scheduler and run:

```bash
MODE=one_bypass
mkdir -p "results/benchmarks/repeated/$MODE"

for seed in 0 1 2 3 4; do
    "$HOME/.venvs/kvadapt-vllm/bin/vllm" bench serve \
        --backend openai \
        --model Qwen/Qwen3-0.6B \
        --dataset-name random \
        --num-prompts 160 \
        --max-concurrency 16 \
        --random-input-len 2048 \
        --random-output-len 128 \
        --random-range-ratio 0.8 \
        --temperature 0 \
        --seed "$seed" \
        --ignore-eos \
        --save-result \
        --save-detailed \
        --result-dir "results/benchmarks/repeated/$MODE" \
        --result-filename "seed_${seed}.json" || break
done
```

Use a different `MODE` for each scheduler to avoid overwriting results.

## Results

The following table compares original vLLM asynchronous scheduling with KVAdapt One-Bypass.

| Metric | vLLM Async | KVAdapt | Change |
|---|---:|---:|---:|
| Output throughput (tokens/s) | 2,159.39 | 2,166.79 | +0.34% |
| Mean TTFT (ms) | 491.90 | 483.40 | -1.73% |
| P99 TTFT (ms) | 802.73 | 882.03 | +9.88% |
| Short-request TTFT (ms) | 473.99 | 402.84 | **-15.01%** |
| Long-request TTFT (ms) | 507.94 | 555.56 | +9.37% |

Short requests have fewer than 2,048 input tokens. Long requests have at least 2,048 input tokens.

Short-request TTFT improved on all five seeds. Long-request TTFT regressed on all five seeds.

The overall throughput difference is small and should not be interpreted as a demonstrated throughput improvement.

The table reports means across five seeds for throughput and overall latency metrics. Length-grouped TTFT values are aggregated across requests in the corresponding groups. P99 TTFT is the mean of per-seed P99 values.

### Bypass Limit Comparison

Allowing two bypasses reduced short-request TTFT by 20.32%, but increased long-request TTFT by 14.59%.

Restricting the policy to one bypass reduced the short-request improvement to 15.01%, while decreasing the long-request regression to 9.37%.

One-Bypass was selected as the default configuration because it provides a better latency trade-off under the evaluated workload.

### Runtime Validation

A diagnostic run of the One-Bypass scheduler recorded:

| Metric | Observed |
|---|---:|
| Scheduling calls | 2,673 |
| Reordering events | 49 |
| Selected requests scheduled | 49 |
| Selected requests not scheduled | 0 |
| Maximum observed bypass count | 1 |

All 160 benchmark requests completed successfully.

These results confirm that reordering occurred during serving and that the observed bypass count respected the configured limit.

## Limitations

KVAdapt is an experimental scheduling policy, not a general replacement for the original vLLM scheduler.

Its measured benefits are specific to the evaluated workload and constrained KV-cache configuration.

Although short-request TTFT improved, longer requests experienced higher latency, and overall P99 TTFT was worse than the baseline.

The current evaluation does not establish improved throughput, fairness across all workloads, or performance benefits with larger KV-cache allocations.

KVAdapt also relies on internal vLLM scheduling interfaces, which may change between versions.

## Project Status

The implementation, admission policy test cases, asynchronous integration, repeated benchmarks, and runtime validation are complete.

The repository is intended as a reproducible systems engineering project for investigating KV-cache-aware request scheduling.