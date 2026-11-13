"""Regression tests for POST /api/render; no Ollama or customer data required.

Run: python -m unittest tests/test_render_validation.py
"""
import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from scopewright_server import Handler

GOOD = {
    "project_title": "<Bathroom>",
    "client_summary": "Replace vanity",
    "sections": [{"name": "Work", "items": [{"description": "Remove vanity",
        "quantity": None, "unit": None, "notes": None}]}],
    "exclusions": [], "allowances": [], "assumptions": [],
    "change_order_terms": "", "open_questions": ["Confirm finish"],
}


class RenderValidationTests(unittest.TestCase):
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

    def render(self, scope):
        conn = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=3)
        try:
            body = json.dumps({"scope": scope})
            conn.request("POST", "/api/render", body=body,
                         headers={"Content-Type": "application/json"})
            response = conn.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            conn.close()

    def test_valid_html_is_escaped(self):
        status, body = self.render(GOOD)
        self.assertEqual(status, 200)
        self.assertIn("&lt;Bathroom&gt;", body)
        self.assertNotIn("<h1><Bathroom></h1>", body)

    def test_invalid_title(self):
        self.assert_invalid(dict(GOOD, project_title=42))

    def test_invalid_sections(self):
        self.assert_invalid(dict(GOOD, sections="wrong"))

    def test_invalid_exclusions(self):
        self.assert_invalid(dict(GOOD, exclusions=[17]))

    def test_invalid_nested_item(self):
        self.assert_invalid(dict(GOOD, sections=[{"name": "Work", "items": [42]}]))

    def assert_invalid(self, scope):
        status, body = self.render(scope)
        self.assertEqual(status, 400)
        self.assertIn("scope is not valid", json.loads(body)["error"])


if __name__ == "__main__":
    unittest.main()
