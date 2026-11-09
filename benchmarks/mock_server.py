import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != '/v1/models':
            self.send_error(404)
            return
        body = json.dumps({'data': [{'id': 'Qwen/Qwen3-0.6B', 'object': 'model'}]}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != '/v1/completions':
            self.send_error(404)
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            payload = json.loads(self.rfile.read(length))
            max_tokens = int(payload['max_tokens'])
            if max_tokens < 1 or not payload.get('stream'):
                raise ValueError('Invalid request')
        except (ValueError, KeyError, TypeError):
            self.send_error(400)
            return
        count = min(max_tokens, 3)
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        for index in range(count):
            time.sleep(0.02 if index == 0 else 0.01)
            self.send_event({'choices': [{'text': f' token{index + 1}'}]})
        self.send_event({'choices': [], 'usage': {'completion_tokens': count}})
        self.wfile.write(b'data: [DONE]\n\n')
        self.wfile.flush()

    def send_event(self, data: dict) -> None:
        self.wfile.write(f'data: {json.dumps(data)}\n\n'.encode())
        self.wfile.flush()

    def log_message(self, format: str, *args: object) -> None:
        return

if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', 8000), MockHandler)
    print('Mock LLM server at http://127.0.0.1:8000', flush=True)
    server.serve_forever()
