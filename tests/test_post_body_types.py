"""Regression tests for non-object JSON request bodies.

These tests are expected to FAIL on main until the 2026-11-15 body-type
audit is addressed. No Ollama, network service, or customer data required.
Run: python -m unittest discover -s tests -p 'test_post_body_types.py'
"""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from scopewright_server import Handler


class PostBodyTypeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request_json(self, path, raw_json):
        conn = http.client.HTTPConnection(
            "127.0.0.1", self.server.server_port, timeout=3
        )
        try:
            conn.request("POST", path, body=raw_json,
                         headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            payload = response.read()
            return response.status, json.loads(payload)
        finally:
            conn.close()

    def assert_bad_body(self, path, raw_json):
        status, payload = self.request_json(path, raw_json)
        self.assertEqual(status, 400)
        self.assertIsInstance(payload, dict)
        self.assertIsInstance(payload.get("error"), str)

    def test_render_array(self):
        self.assert_bad_body("/api/render", "[]")

    def test_render_null(self):
        self.assert_bad_body("/api/render", "null")

    def test_scopes_string(self):
        # Should reject before any save_scope call.
        self.assert_bad_body("/api/scopes", '"hello"')

    def test_generate_boolean(self):
        # Should reject before any Ollama invocation.
        self.assert_bad_body("/api/generate", "true")

    def test_valid_object_keeps_existing_render_error(self):
        status, payload = self.request_json("/api/render", "{}")
        self.assertEqual(status, 400)
        self.assertEqual(payload.get("error"), "scope must be an object")


if __name__ == "__main__":
    unittest.main()
