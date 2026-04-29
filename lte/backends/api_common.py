from __future__ import annotations

import json
import os
import ssl
from urllib import error, request

import certifi


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def post_json(*, url: str, payload: dict, headers: dict[str, str], timeout_sec: int = 120) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(url=url, data=body, headers=headers, method="POST")
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    try:
        with request.urlopen(req, timeout=timeout_sec, context=ssl_context) as resp:
            raw = resp.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {detail}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc.reason}") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON response from {url}: {raw[:500]}") from exc
