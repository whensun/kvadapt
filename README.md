
# KVAdapt

Adaptive KV-Cache Management for Efficient LLM Serving

## Overview

KVAdapt is an open-source project for investigating and optimizing KV-cache management and scheduling in LLM serving systems.

The project focuses on identifying performance bottlenecks in vLLM and developing practical optimizations for different inference workloads.

## Goals

- Improve aggregate output throughput (tokens/sec).
- Reduce inference latency (TTFT, TPOT, and ITL).
- Improve GPU memory and KV-cache utilization.
- Evaluate performance under different workloads.
- Compare optimized vLLM against standard vLLM and SGLang.

## Methodology

1. Establish reproducible inference benchmarks.
2. Profile KV-cache management and scheduling bottlenecks.
3. Implement targeted optimizations.
4. Evaluate throughput, latency, and memory efficiency.
5. Compare results against existing implementations.

## Frameworks

- vLLM: Primary implementation framework.
- SGLang: Additional performance baseline.
- PyTorch: Runtime and profiling tools.

## Status

Early development. Performance improvements have not yet been established.
