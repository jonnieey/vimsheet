"""Low-level HTTP fetch helpers — no Textual or VimSheet model imports."""

from __future__ import annotations

import json
import os
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


# --------------------------------------------------------------------------- #
# Curl-command parser — copy a curl command into a formula and it just works.  #
# --------------------------------------------------------------------------- #

_ENV_VAR_RE = re.compile(r"\$(\w+)|\$\{(\w+)\}")


def _resolve_env_vars(text: str) -> str:
    """Replace ``$VARNAME`` and ``${VARNAME}`` with ``os.environ`` values."""

    def _repl(m: re.Match) -> str:
        name = m.group(1) or m.group(2)
        return os.environ.get(name, "")

    return _ENV_VAR_RE.sub(_repl, text)


def _tokenize_curl(cmd: str) -> list[str]:
    """Simple shell-style tokenizer that respects ``'`` and ``"`` quoting."""
    tokens: list[str] = []
    i = 0
    while i < len(cmd):
        ch = cmd[i]
        if ch in (" ", "\t"):
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            i += 1
            start = i
            while i < len(cmd) and cmd[i] != quote:
                i += 1
            tokens.append(cmd[start:i])
            i += 1
        else:
            start = i
            while i < len(cmd) and cmd[i] not in (" ", "\t"):
                i += 1
            tokens.append(cmd[start:i])
    return tokens


def parse_curl_command(cmd: str) -> dict[str, Any]:
    """Parse a curl command string into *url*, *headers*, and *method*.

    Parameters
    ----------
    cmd : str
        A command that starts with ``curl``, e.g.::

            curl -H "Authorization: Bearer $TOKEN" https://api.example.com/data

    Returns
    -------
    dict
        ``{"url": ..., "headers": {"Key": "Value", ...}, "method": "GET"}``

    Environment variables (``$VAR``, ``${VAR}``) are resolved from
    ``os.environ`` before parsing.
    """
    cmd = _resolve_env_vars(cmd.strip())

    if cmd.lower().startswith("curl "):
        cmd = cmd[5:]

    tokens = _tokenize_curl(cmd)

    headers: dict[str, str] = {}
    method: str = "GET"
    url: str = ""
    url_found = False

    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in ("-H", "--header"):
            i += 1
            if i < len(tokens):
                header_line = tokens[i]
                if ":" in header_line:
                    k, v = header_line.split(":", 1)
                    headers[k.strip()] = v.strip()
            i += 1
        elif t in ("-X", "--request"):
            i += 1
            if i < len(tokens):
                method = tokens[i].upper()
            i += 1
        elif t in ("-d", "--data", "--data-raw"):
            i += 2
        elif t.startswith("-"):
            i += 1
            if i < len(tokens) and not tokens[i].startswith("-"):
                i += 1
        else:
            if not url_found:
                url = t
                url_found = True
            i += 1

    return {"url": url, "headers": headers, "method": method}


# --------------------------------------------------------------------------- #
# HTTP fetch                                                                   #
# --------------------------------------------------------------------------- #


def do_fetch(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    method: str = "GET",
) -> FetchResult:
    """Blocking HTTP request.  Tries ``requests`` first, falls back to ``urllib``."""
    hdrs = dict(headers) if headers else {}
    hdrs.setdefault("User-Agent", "VimSheet/1.0")

    try:
        import requests  # type: ignore[import-untyped]

        try:
            meth = method.lower()
            if meth == "get":
                resp = requests.get(url, headers=hdrs, timeout=timeout, stream=True)
            elif meth == "post":
                resp = requests.post(url, headers=hdrs, timeout=timeout, stream=True)
            elif meth == "put":
                resp = requests.put(url, headers=hdrs, timeout=timeout, stream=True)
            elif meth == "delete":
                resp = requests.delete(url, headers=hdrs, timeout=timeout, stream=True)
            elif meth == "patch":
                resp = requests.patch(url, headers=hdrs, timeout=timeout, stream=True)
            elif meth == "head":
                resp = requests.head(url, headers=hdrs, timeout=timeout)
            else:
                resp = requests.get(url, headers=hdrs, timeout=timeout, stream=True)

            if method.upper() != "HEAD":
                raw = b""
                for chunk in resp.iter_content(65536):
                    raw += chunk
                    if len(raw) > MAX_RESPONSE_BYTES:
                        return FetchResult(None, resp.status_code, "#TOOBIG")
            else:
                raw = b""

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
        req = urllib.request.Request(url, headers=hdrs, method=method)
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
