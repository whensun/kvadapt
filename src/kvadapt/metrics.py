
def output_throughput(output_tokens: int, duration_seconds: float) -> float:
    if output_tokens < 0:
        raise ValueError('output_tokens must be non-negative')
    if duration_seconds <= 0:
        raise ValueError('duration_seconds must be positive')
    return output_tokens / duration_seconds
