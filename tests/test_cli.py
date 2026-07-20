import http.client
import json
import subprocess
import threading
import unittest
from pathlib import Path

from src.app import create_server

ROOT = Path(__file__).resolve().parents[1]


class CLITest(unittest.TestCase):
    def setUp(self):
        self.server = create_server(port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.hostname = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def cli(self, *args):
        result = subprocess.run(
            ["./bin/appctl", "--hostname", self.hostname, *args, "-o", "json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        return json.loads(result.stdout) if result.stdout else None

    def cli_failure(self, *args):
        result = subprocess.run(
            ["./bin/appctl", "--hostname", self.hostname, *args, "-o", "json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(result.returncode, 0)
        return json.loads(result.stderr)["error"]["message"]

    def test_generated_cli_is_the_application_acceptance_surface(self):
        self.assertEqual(self.cli("health", "get"), {"status": "ok"})
        created = self.cli("tasks", "create", "--set", "title=Ship from the CLI")
        self.assertEqual(created, {"id": "1", "title": "Ship from the CLI", "completed": False})
        self.assertEqual(self.cli("tasks", "list"), [created])
        self.assertEqual(self.cli("tasks", "get", "--id", created["id"]), created)
        updated = self.cli("tasks", "update", "--id", created["id"], "--set", "completed=true")
        self.assertEqual(updated, {**created, "completed": True})
        self.cli("tasks", "delete", "--id", created["id"])
        self.assertEqual(self.cli("tasks", "list"), [])

    def test_generated_cli_surfaces_api_errors(self):
        self.assertIn("HTTP 400", self.cli_failure("tasks", "create", "--set-str", "title="))
        self.assertIn("HTTP 404", self.cli_failure("tasks", "get", "--id", "missing"))
        task = self.cli("tasks", "create", "--set", "title=Keep the contract honest")
        error = self.cli_failure("tasks", "update", "--id", task["id"], "--file", "test/empty.json")
        self.assertIn("title or completed is required", error)

    def test_http_boundary_rejects_unsupported_input(self):
        status, headers, _ = self.request("PUT", "/tasks")
        self.assertEqual(status, 405)
        self.assertEqual(headers["allow"], "GET, POST")

        status, _, body = self.request("POST", "/tasks", "text/plain", {"title": "wrong media type"})
        self.assertEqual(status, 400)
        self.assertEqual(body, {"error": "content-type must be application/json"})

        status, _, body = self.request("POST", "/tasks", "application/json", {"title": "x" * 1_000_001})
        self.assertEqual(status, 400)
        self.assertEqual(body, {"error": "request body exceeds 1 MB"})

    def request(self, method, path, content_type=None, body=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        data = None if body is None else json.dumps(body)
        headers = {} if content_type is None else {"content-type": content_type}
        connection.request(method, path, data, headers)
        response = connection.getresponse()
        payload = response.read()
        result = None if not payload else json.loads(payload)
        headers = {name.lower(): value for name, value in response.getheaders()}
        connection.close()
        return response.status, headers, result


if __name__ == "__main__":
    unittest.main()

