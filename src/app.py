import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlsplit

MAX_BODY_SIZE = 1_000_000


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self._send(200, {"status": "ok"})
            return
        if path == "/tasks":
            with self.server.lock:
                tasks = list(self.server.tasks.values())
            self._send(200, tasks)
            return
        task_id = self._task_id(path)
        if task_id is None:
            self._send(404, {"error": "not found"})
            return
        with self.server.lock:
            task = self.server.tasks.get(task_id)
        self._send(200, task) if task else self._send(404, {"error": "task not found"})

    def do_POST(self):
        if urlsplit(self.path).path != "/tasks":
            self._unsupported_or_missing()
            return
        try:
            body = self._read_json()
        except ValueError as error:
            self._send(400, {"error": str(error)})
            return
        title = body.get("title")
        if not isinstance(title, str) or not title.strip():
            self._send(400, {"error": "title is required"})
            return
        with self.server.lock:
            task_id = str(self.server.next_id)
            self.server.next_id += 1
            task = {"id": task_id, "title": title.strip(), "completed": False}
            self.server.tasks[task_id] = task
        self._send(201, task)

    def do_PATCH(self):
        task_id = self._task_id(urlsplit(self.path).path)
        if task_id is None:
            self._unsupported_or_missing()
            return
        try:
            body = self._read_json()
        except ValueError as error:
            self._send(400, {"error": str(error)})
            return
        if "title" not in body and "completed" not in body:
            self._send(400, {"error": "title or completed is required"})
            return
        if "title" in body and (not isinstance(body["title"], str) or not body["title"].strip()):
            self._send(400, {"error": "title must be a non-empty string"})
            return
        if "completed" in body and not isinstance(body["completed"], bool):
            self._send(400, {"error": "completed must be a boolean"})
            return
        with self.server.lock:
            task = self.server.tasks.get(task_id)
            if task:
                if "title" in body:
                    task["title"] = body["title"].strip()
                if "completed" in body:
                    task["completed"] = body["completed"]
        self._send(200, task) if task else self._send(404, {"error": "task not found"})

    def do_DELETE(self):
        task_id = self._task_id(urlsplit(self.path).path)
        if task_id is None:
            self._unsupported_or_missing()
            return
        with self.server.lock:
            task = self.server.tasks.pop(task_id, None)
        self._send(204) if task else self._send(404, {"error": "task not found"})

    def do_PUT(self):
        self._unsupported_or_missing()

    def _unsupported_or_missing(self):
        path = urlsplit(self.path).path
        if path == "/tasks":
            self._send(405, {"error": "method not allowed"}, {"Allow": "GET, POST"})
        elif self._task_id(path) is not None:
            self._send(405, {"error": "method not allowed"}, {"Allow": "GET, PATCH, DELETE"})
        else:
            self._send(404, {"error": "not found"})

    def _read_json(self):
        if self.headers.get_content_type() != "application/json":
            raise ValueError("content-type must be application/json")
        try:
            length = int(self.headers.get("content-length", "0"))
        except ValueError as error:
            raise ValueError("invalid content-length") from error
        if length < 0:
            raise ValueError("invalid content-length")
        if length > MAX_BODY_SIZE:
            remaining = length
            while remaining:
                chunk = self.rfile.read(min(remaining, 64 * 1024))
                if not chunk:
                    break
                remaining -= len(chunk)
            raise ValueError("request body exceeds 1 MB")
        try:
            body = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            detail = error.msg if isinstance(error, json.JSONDecodeError) else str(error)
            raise ValueError(f"invalid JSON: {detail}") from error
        if not isinstance(body, dict):
            raise ValueError("request body must be a JSON object")
        return body

    @staticmethod
    def _task_id(path):
        parts = path.split("/")
        return unquote(parts[2]) if len(parts) == 3 and parts[1] == "tasks" and parts[2] else None

    def _send(self, status, body=None, headers=None):
        data = b"" if body is None else json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


def create_server(host="127.0.0.1", port=3000):
    server = ThreadingHTTPServer((host, port), AppHandler)
    server.tasks = {}
    server.next_id = 1
    server.lock = threading.Lock()
    return server
