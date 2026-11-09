
import json

import httpx
import pytest
from kvadapt.benchmark import load_workload, percentile, run_benchmark

def mock_server(request: httpx.Request) -> httpx.Response:
    payload = json.loads(request.content)
    assert payload['stream_options']['include_usage'] is True
    events = [
        {'choices': [{'text': 'hello'}]},
        {'choices': [{'text': ' world'}]},
        {'choices': [], 'usage': {'completion_tokens': 2}},
    ]
    text = ''.join(f'data: {json.dumps(event)}\n\n' for event in events) + 'data: [DONE]\n\n'
    return httpx.Response(200, text=text, headers={'content-type': 'text/event-stream'})

def test_mock_benchmark():
    requests = [
        {'request_id': 0, 'prompt': 'one', 'max_tokens': 4},
        {'request_id': 1, 'prompt': 'two', 'max_tokens': 4},
    ]
    summary = run_benchmark(requests, 'http://localhost:8000', 'test-model', 2, httpx.MockTransport(mock_server))
    assert summary['requests'] == 2
    assert summary['output_tokens'] == 4
    assert summary['output_tokens_per_second'] > 0
    assert summary['mean_ttft_ms'] is not None
    assert all(result['output_tokens'] == 2 for result in summary['results'])

def test_percentile():
    assert percentile([5, 1, 3, 2, 4], 99) == 5
    assert percentile([], 99) is None

def test_invalid_concurrency():
    with pytest.raises(ValueError):
        run_benchmark([{'request_id': 0}], 'http://localhost', 'test', 0)

def test_missing_usage():
    def handler(request):
        return httpx.Response(200, text='data: {"choices": [{"text": "hi"}]}\n\ndata: [DONE]\n\n')
    with pytest.raises(ValueError, match='completion_tokens'):
        run_benchmark([{'request_id': 0, 'prompt': 'hi', 'max_tokens': 3}], 'http://localhost', 'test', 1, httpx.MockTransport(handler))

def test_load_workload(tmp_path):
    path = tmp_path / 'input.jsonl'
    path.write_text('{"request_id": 0}\n{"request_id": 1}\n')
    assert len(load_workload(path)) == 2
