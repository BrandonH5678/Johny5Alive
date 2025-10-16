import time
import random
import requests

DEFAULT_UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

class Response:
    def __init__(self, r):
        self.url = getattr(r, "url", "")
        self.status_code = getattr(r, "status_code", 0)
        self.headers = dict(getattr(r, "headers", {}))
        self.text = getattr(r, "text", "")

class RobustWebFetcher:
    """Hardened HTTP layer: randomized UA, retries/backoff, simple proxy support.
    If you already have an RWF implementation in J5A, you can swap this out.
    """
    def __init__(self, timeout=25, max_retries=3, proxies=None):
        self.s = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.proxies = proxies or {}
        self.transient = {429, 500, 502, 503, 504}

    def _headers(self, extra=None):
        h = {
            "User-Agent": random.choice(DEFAULT_UAS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        if extra: h.update(extra)
        return h

    def get(self, url, **kw) -> Response:
        hdrs = self._headers(kw.pop("headers", None))
        delay = 1.0
        last = None
        for _ in range(self.max_retries):
            try:
                r = self.s.get(url, headers=hdrs, timeout=self.timeout, allow_redirects=True, proxies=self.proxies, **kw)
                if r.status_code in self.transient:
                    time.sleep(delay); delay *= 2; continue
                return Response(r)
            except Exception as e:
                last = e; time.sleep(delay); delay *= 2
        raise RuntimeError(f"GET failed for {url}: {last}")

    def head(self, url, **kw) -> Response:
        hdrs = self._headers(kw.pop("headers", None))
        delay = 1.0
        last = None
        for _ in range(self.max_retries):
            try:
                r = self.s.head(url, headers=hdrs, timeout=self.timeout, allow_redirects=True, proxies=self.proxies, **kw)
                if r.status_code in self.transient:
                    time.sleep(delay); delay *= 2; continue
                return Response(r)
            except Exception as e:
                last = e; time.sleep(delay); delay *= 2
        raise RuntimeError(f"HEAD failed for {url}: {last}")

    # convenience
    def head_ok(self, url, content_types=None, min_bytes=0):
        try:
            r = self.head(url)
            if r.status_code >= 400:
                return False
            ctype = r.headers.get("Content-Type", "").lower()
            clen = r.headers.get("Content-Length", "")
            ok_type = True
            if content_types:
                ok_type = any(ctype.startswith(ct) for ct in content_types)
            ok_len = True
            if min_bytes and clen.isdigit():
                ok_len = int(clen) >= min_bytes
            return ok_type and ok_len
        except Exception:
            return False
