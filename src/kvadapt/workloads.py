
import json
import random
from pathlib import Path

def make_prefix(group_id: int, word_count: int) -> str:
    if word_count <= 0:
        raise ValueError('word_count must be positive')
    text = f'Context group {group_id}. The inference server processes requests and maintains key value cache blocks for attention computation.'
    words = text.split()
    return ' '.join((words * (word_count // len(words) + 1))[:word_count])

def build_workload(count: int, shared_fraction: float, prefix_groups: int = 4, prefix_words: int = 256, output_tokens: int = 64, seed: int = 42) -> list[dict]:
    if count <= 0 or prefix_groups <= 0 or prefix_words <= 0 or output_tokens <= 0:
        raise ValueError('count, prefix_groups, prefix_words, and output_tokens must be positive')
    if not 0 <= shared_fraction <= 1:
        raise ValueError('shared_fraction must be between 0 and 1')
    rng = random.Random(seed)
    shared_count = round(count * shared_fraction)
    requests = []
    for index in range(count):
        is_shared = index < shared_count
        group_id = index % prefix_groups if is_shared else prefix_groups + index
        prefix = make_prefix(group_id, prefix_words)
        requests.append({
            'request_id': index,
            'prefix_group': group_id if is_shared else None,
            'prompt': f'{prefix}\nQuestion {index}: Explain the effect of caching and scheduling on latency.',
            'max_tokens': output_tokens,
        })
    rng.shuffle(requests)
    return requests

def write_workload(path: Path, requests: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as file:
        for request in requests:
            file.write(json.dumps(request, ensure_ascii=False) + '\n')
