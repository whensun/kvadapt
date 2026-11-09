from collections import Counter

def audit_workload(requests: list[dict]) -> dict:
    if not requests:
        raise ValueError('workload must not be empty')
    ids = set()
    prefixes = []
    groups = {}
    shared_count = 0
    output_budget = 0
    for request in requests:
        request_id = request.get('request_id')
        prompt = request.get('prompt')
        output_tokens = request.get('max_tokens')
        group = request.get('prefix_group')
        if not isinstance(request_id, int) or request_id in ids:
            raise ValueError('request_id must be a unique integer')
        if not isinstance(prompt, str) or '\nQuestion ' not in prompt:
            raise ValueError('prompt must contain a Question separator')
        if not isinstance(output_tokens, int) or output_tokens <= 0:
            raise ValueError('max_tokens must be a positive integer')
        if group is not None and not isinstance(group, int):
            raise ValueError('prefix_group must be an integer or None')
        ids.add(request_id)
        prefix = prompt.split('\nQuestion ', 1)[0]
        prefixes.append(prefix)
        output_budget += output_tokens
        if group is not None:
            shared_count += 1
            if group in groups and groups[group] != prefix:
                raise ValueError('same prefix_group contains different prefixes')
            groups[group] = prefix
    counts = Counter(prefixes)
    return {
        'requests': len(requests),
        'unique_prefixes': len(counts),
        'declared_shared_requests': shared_count,
        'requests_with_repeated_prefix': sum(count for count in counts.values() if count > 1),
        'repeat_occurrences_after_first': sum(count - 1 for count in counts.values() if count > 1),
        'max_output_tokens_total': output_budget,
    }
