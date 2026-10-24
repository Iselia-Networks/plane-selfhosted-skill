import importlib.util
import io
import json
import os
from pathlib import Path
import unittest
import urllib.error
import urllib.request
from unittest.mock import Mock, patch

SCRIPT = Path(__file__).resolve().parents[1] / "skills/plane-selfhosted/scripts/plane_api.py"
SPEC = importlib.util.spec_from_file_location("plane_api", SCRIPT)
api = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(api)


class ClientTests(unittest.TestCase):
    def test_roots_and_versions(self):
        for base in ("https://plane.example.com", "https://plane.example.com/", "https://plane.example.com/api/v1/"):
            self.assertEqual(api.api_root(base), "https://plane.example.com/api/v1/")
        self.assertEqual(api.api_root("https://example.com/plane", "v2"), "https://example.com/plane/api/v2/")
        self.assertEqual(api.api_root("https://example.com/api/v2"), "https://example.com/api/v2/")
        with self.assertRaises(api.ApiError):
            api.api_root("https://example.com/api/v2", "v1")

    def test_reject_unsafe_target(self):
        for base in ("http://example.com", "https://key@example.com", "https://example.com?key=secret"):
            with self.subTest(base=base), self.assertRaises(api.ApiError):
                api.api_root(base)
        for endpoint in ("https://evil.example/x", "//evil.example/x", "../x", "%2e%2e/x", "x/../y", "x\\y", "x#fragment", "x\n"):
            with self.subTest(endpoint=endpoint), self.assertRaises(api.ApiError):
                api.endpoint_url("https://example.com/api/v1/", endpoint)

    def client(self):
        client = api.Client("https://plane.example.com/api/v1/", "test-secret", max_retry_wait=0)
        client.opener = Mock()
        return client

    def response(self, value):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps(value).encode()
        return response

    def error(self, status):
        return urllib.error.HTTPError("https://example.com", status, "error", {"Retry-After": "0"}, io.BytesIO(b"secret"))

    def test_reads_retry_and_send_header(self):
        client = self.client()
        client.opener.open.side_effect = [self.error(429), self.response({"ok": True})]
        with patch.object(api.time, "sleep"):
            self.assertEqual(client.request("GET", "users/me/"), {"ok": True})
        self.assertEqual(client.opener.open.call_count, 2)
        self.assertEqual(client.opener.open.call_args.args[0].get_header("X-api-key"), "test-secret")

    def test_write_is_never_retried(self):
        for failure in (self.error(429), self.error(503), urllib.error.URLError("timeout")):
            client = self.client()
            client.opener.open.side_effect = failure
            with self.assertRaises(api.ApiError):
                client.request("POST", "workspaces/demo/projects/", {"name": "Example"})
            self.assertEqual(client.opener.open.call_count, 1)

    def test_redirect_handler_never_forwards_key(self):
        request = urllib.request.Request("https://plane.example.com/", headers={"X-Api-Key": "test-secret"})
        self.assertIsNone(api.NoRedirect().redirect_request(request, None, 302, "", {}, "https://evil.example/"))
        client = self.client()
        client.opener.open.side_effect = self.error(302)
        with self.assertRaises(api.ApiError):
            client.request("GET", "users/me/")
        self.assertEqual(client.opener.open.call_count, 1)

    def test_cursor_pagination(self):
        client = self.client()
        client.request = Mock(side_effect=[
            {"results": [1], "next_page_results": True, "next_cursor": "10:1:0"},
            {"results": [2], "next_page_results": False},
        ])
        self.assertEqual(client.paginate("workspaces/demo/projects/?per_page=1", 10), [1, 2])
        self.assertIn("cursor=10%3A1%3A0", client.request.call_args.args[1])
        self.assertIn("per_page=1", client.request.call_args.args[1])

    def test_offset_next_link(self):
        client = self.client()
        client.request = Mock(side_effect=[
            {"results": [1], "next": "https://plane.example.com/api/v1/workspaces/demo/projects/?offset=1"},
            {"results": [2], "next": None},
        ])
        self.assertEqual(client.paginate("workspaces/demo/projects/", 3), [1, 2])

    def test_pagination_guards(self):
        for pages in (
            [{"results": [1]}],
            [{"results": [1], "next": "https://evil.example/projects/"}],
            [{"results": [1], "next_page_results": True, "next_cursor": "same"}] * 3,
        ):
            client = self.client()
            client.request = Mock(side_effect=pages)
            with self.assertRaises(api.ApiError):
                client.paginate("workspaces/demo/projects/", 3)
        client.request = Mock(return_value={"results": [], "next_page_results": True, "next_cursor": "next"})
        with self.assertRaisesRegex(api.ApiError, "max-pages"):
            client.paginate("workspaces/demo/projects/", 1)

    def test_cli_invalid_json_does_not_echo_body(self):
        with patch.dict(os.environ, {"PLANE_BASE_URL": "https://example.com", "PLANE_API_KEY": "test-secret"}), patch.object(api.sys, "stdin", io.StringIO("test-secret")), patch.object(api.sys, "stderr", io.StringIO()) as error:
            self.assertEqual(api.main(["POST", "users/me/", "--body-file", "-"]), 1)
            self.assertNotIn("test-secret", error.getvalue())
            self.assertIn("valid JSON", error.getvalue())

    def test_retry_after_budget(self):
        client = self.client()
        client.opener.open.side_effect = urllib.error.HTTPError("https://example.com", 429, "", {"Retry-After": "60"}, None)
        with self.assertRaises(api.ApiError), patch.object(api.time, "sleep") as sleep:
            client.request("GET", "users/me/")
        sleep.assert_not_called()
        self.assertEqual(client.opener.open.call_count, 1)


if __name__ == "__main__":
    unittest.main()
