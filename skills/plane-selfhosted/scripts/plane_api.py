#!/usr/bin/env python3
"""Small dependency-free Plane REST client. Python 3.10+."""

import argparse
import email.utils
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


class ApiError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def api_root(base, version=None):
    parsed = urllib.parse.urlsplit(base)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise ApiError("PLANE_BASE_URL must be an HTTPS origin or API root without credentials/query/fragment")
    if version not in (None, "v1", "v2"):
        raise ApiError("API version must be v1 or v2")
    path = parsed.path.rstrip("/")
    match = re.search(r"/api/(v[12])$", path)
    if match:
        if version and version != match[1]:
            raise ApiError("API version conflicts with PLANE_BASE_URL")
    else:
        path += "/api/" + (version or "v1")
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, path + "/", "", ""))


def endpoint_url(root, endpoint):
    parsed = urllib.parse.urlsplit(endpoint)
    decoded = urllib.parse.unquote(parsed.path)
    if (parsed.scheme or parsed.netloc or parsed.fragment or endpoint.startswith("/")
            or "\\" in decoded or any(ord(c) < 32 for c in endpoint + decoded)
            or any(p in (".", "..") for p in decoded.split("/"))):
        raise ApiError("Endpoint must be a relative API path without traversal or fragments")
    return root + endpoint


def retry_delay(value, attempt):
    if not value:
        return min(2 ** attempt, 8)
    try:
        return max(0, float(value))
    except ValueError:
        try:
            date = email.utils.parsedate_to_datetime(value)
            return max(0, (date - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError):
            return min(2 ** attempt, 8)


class Client:
    def __init__(self, root, key, timeout=30, retries=2, max_retry_wait=10):
        self.root, self.key = root, key
        self.timeout, self.retries, self.max_retry_wait = timeout, retries, max_retry_wait
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, method, endpoint, body=None):
        url = endpoint_url(self.root, endpoint)
        headers = {"X-Api-Key": self.key, "Accept": "application/json"}
        data = None if body is None else json.dumps(body).encode("utf-8")
        if data is not None:
            headers["Content-Type"] = "application/json"
        for attempt in range(self.retries + 1):
            try:
                request = urllib.request.Request(url, data=data, headers=headers, method=method)
                with self.opener.open(request, timeout=self.timeout) as response:
                    raw = response.read()
                    if not raw or method == "HEAD":
                        return None
                    try:
                        return json.loads(raw)
                    except (ValueError, UnicodeError) as exc:
                        raise ApiError("Server returned a non-JSON response") from exc
            except urllib.error.HTTPError as exc:
                status, retry_after = exc.code, exc.headers.get("Retry-After")
                exc.close()
                delay = retry_delay(retry_after, attempt)
                if (method in ("GET", "HEAD") and status in (429, 500, 502, 503, 504)
                        and attempt < self.retries and delay <= self.max_retry_wait):
                    time.sleep(delay)
                    continue
                # Do not echo remote bodies, headers, URLs or keys into diagnostics.
                raise ApiError(f"HTTP {status}; redirects are blocked; reconcile uncertain writes before retrying") from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                if method in ("GET", "HEAD") and attempt < self.retries:
                    time.sleep(min(2 ** attempt, self.max_retry_wait))
                    continue
                raise ApiError("Network request failed; reconcile uncertain writes before retrying") from exc

    def paginate(self, endpoint, max_pages):
        parsed = urllib.parse.urlsplit(endpoint)
        query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
        seen, items = set(), []
        for _ in range(max_pages):
            page_endpoint = urllib.parse.urlunsplit(("", "", parsed.path, urllib.parse.urlencode(query), ""))
            if page_endpoint in seen:
                raise ApiError("Pagination loop detected")
            seen.add(page_endpoint)
            page = self.request("GET", page_endpoint)
            if isinstance(page, list):
                return items + page
            if not isinstance(page, dict) or not isinstance(page.get("results"), list):
                raise ApiError("Unsupported pagination envelope; inspect the response contract")
            items.extend(page["results"])
            if "next_page_results" in page:
                if page["next_page_results"] is False:
                    return items
                cursor = page.get("next_cursor")
                if page["next_page_results"] is not True or not isinstance(cursor, str) or not cursor:
                    raise ApiError("Invalid cursor pagination envelope")
                query["cursor"] = cursor
            elif "next" in page:
                if page["next"] is None:
                    return items
                following = urllib.parse.urljoin(self.root, str(page["next"]))
                target = urllib.parse.urlsplit(following)
                current = urllib.parse.urlsplit(endpoint_url(self.root, endpoint))
                if (target.scheme, target.netloc, target.path) != (current.scheme, current.netloc, current.path):
                    raise ApiError("Pagination next URL changes the API target")
                query = dict(urllib.parse.parse_qsl(target.query, keep_blank_values=True))
            else:
                raise ApiError("No supported pagination marker; refusing possibly truncated results")
        raise ApiError("Pagination exceeded --max-pages; no partial result emitted")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("method", choices=("GET", "HEAD", "POST", "PATCH", "PUT", "DELETE"))
    parser.add_argument("endpoint", help="Relative API path, optionally with query parameters")
    parser.add_argument("--api-version", choices=("v1", "v2"), default=os.environ.get("PLANE_API_VERSION"))
    parser.add_argument("--body-file", help="JSON file, or - for stdin")
    parser.add_argument("--paginate", action="store_true")
    parser.add_argument("--max-pages", type=int, default=1000)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--max-retry-wait", type=float, default=10)
    args = parser.parse_args(argv)
    try:
        if args.timeout <= 0 or args.retries < 0 or args.max_pages <= 0 or args.max_retry_wait < 0:
            raise ApiError("Timeout/page limit must be positive; retries/wait must be nonnegative")
        if args.paginate and args.method != "GET":
            raise ApiError("--paginate is GET-only")
        if args.body_file and args.method in ("GET", "HEAD"):
            raise ApiError("GET/HEAD must not have a request body")
        key = os.environ.get("PLANE_API_KEY", "")
        if not key:
            raise ApiError("Set PLANE_API_KEY using the host's secret mechanism")
        root = api_root(os.environ.get("PLANE_BASE_URL", ""), args.api_version)
        body = None
        if args.body_file:
            raw = sys.stdin.read() if args.body_file == "-" else Path(args.body_file).read_text(encoding="utf-8")
            try:
                body = json.loads(raw)
            except ValueError as exc:
                raise ApiError("Request body must be valid JSON") from exc
        client = Client(root, key, args.timeout, args.retries, args.max_retry_wait)
        result = client.paginate(args.endpoint, args.max_pages) if args.paginate else client.request(args.method, args.endpoint, body)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ApiError, OSError, ValueError) as exc:
        # Filesystem/URL errors may embed sensitive input; expose only controlled messages.
        message = str(exc) if isinstance(exc, ApiError) else "Invalid configuration or unreadable body file"
        key = os.environ.get("PLANE_API_KEY")
        if key:
            message = message.replace(key, "[redacted]")
        print(json.dumps({"error": message}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
