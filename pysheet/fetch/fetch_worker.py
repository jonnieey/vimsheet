"""Low-level HTTP fetch helpers — no Textual or PySheet model imports."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

MAX_RESPONSE_BYTES = 512 * 1024  # 512 KB hard cap
ARRAY_SPILL_CAP = 1000
DEFAULT_TIMEOUT = 10.0


@dataclass
class FetchResult:
    raw: bytes | None
    status_code: int | None
    error: str | None  # None = success; set to a sentinel string on failure

    @property
    def ok(self) -> bool:
        return self.error is None and self.raw is not None


def do_fetch(url: str, timeout: float = DEFAULT_TIMEOUT) -> FetchResult:
    """Blocking HTTP GET.  Tries requests first, falls back to urllib."""
    try:
        import requests  # type: ignore[import-untyped]

        try:
            resp = requests.get(url, timeout=timeout, stream=True)
            raw = b""
            for chunk in resp.iter_content(65536):
                raw += chunk
                if len(raw) > MAX_RESPONSE_BYTES:
                    return FetchResult(None, resp.status_code, "#TOOBIG")
            if not resp.ok:
                return FetchResult(None, resp.status_code, f"#HTTP:{resp.status_code}")
            return FetchResult(raw, resp.status_code, None)
        except requests.Timeout:
            return FetchResult(None, None, "#TIMEOUT")
        except requests.ConnectionError:
            return FetchResult(None, None, "#FETCH")
        except Exception:
            return FetchResult(None, None, "#FETCH")

    except ImportError:
        pass

    # urllib fallback (always available)
    import urllib.error
    import urllib.request

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "PySheet/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                return FetchResult(None, r.status, "#TOOBIG")
            return FetchResult(raw, r.status, None)
    except urllib.error.HTTPError as e:
        return FetchResult(None, e.code, f"#HTTP:{e.code}")
    except urllib.error.URLError:
        return FetchResult(None, None, "#FETCH")
    except TimeoutError:
        return FetchResult(None, None, "#TIMEOUT")
    except Exception:
        return FetchResult(None, None, "#FETCH")


def parse_response(result: FetchResult) -> Any:
    """Parse a successful FetchResult into a Python object.

    Tries JSON first; returns the raw text string on JSON parse failure.
    """
    if not result.ok or result.raw is None:
        return result.error
    text = result.raw.decode("utf-8", errors="replace").strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return text


_TOKEN_RE = re.compile(r"(\w+)|\[(\d+)\]")


def extract_json_path(data: Any, path: str) -> Any:
    """Traverse *data* using dot-and-bracket notation.

    Examples:
        ""                    → data unchanged
        "price"               → data["price"]
        "data.price"          → data["data"]["price"]
        "items[0].name"       → data["items"][0]["name"]

    Raises KeyError / IndexError / TypeError on invalid paths.
    """
    if not path:
        return data
    current = data
    for m in _TOKEN_RE.finditer(path):
        key, idx = m.group(1), m.group(2)
        current = current[key] if key else current[int(idx)]
    return current
