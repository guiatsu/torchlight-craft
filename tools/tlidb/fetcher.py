"""Polite, cached HTTP access to public TLIDB HTML pages."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
from urllib.request import Request, urlopen


TLIDB_HOST = "tlidb.com"
ROBOTS_URL = "https://tlidb.com/robots.txt"
USER_AGENT = "TorchlightCraftPlannerCatalog/0.2 (+https://github.com/guiatsu/torchlight-craft)"
RETRYABLE_STATUS = {429, 500, 502, 503, 504}
MAX_PAGE_BYTES = 12 * 1024 * 1024


class FetchError(RuntimeError):
    """A source page could not be fetched or validated."""


@dataclass(frozen=True, slots=True)
class FetchedPage:
    url: str
    html: str
    retrieved_at: str
    sha256: str
    status_code: int
    from_cache: bool
    headers: dict[str, str]


class PageFetcher:
    def __init__(
        self,
        cache_dir: Path,
        *,
        offline: bool = False,
        minimum_interval: float = 1.0,
        timeout: float = 25.0,
        retries: int = 2,
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.offline = offline
        self.minimum_interval = max(0.0, minimum_interval)
        self.timeout = timeout
        self.retries = retries
        self._last_request_at = 0.0
        self._robots: RobotFileParser | None = None
        self._robots_retrieved_at = ""

    @staticmethod
    def _url_key(url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _paths(self, url: str) -> tuple[Path, Path]:
        key = self._url_key(url)
        return self.cache_dir / f"{key}.html", self.cache_dir / f"{key}.json"

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    def _rate_limit(self) -> None:
        delay = self.minimum_interval - (time.monotonic() - self._last_request_at)
        if delay > 0:
            time.sleep(delay)
        self._last_request_at = time.monotonic()

    def _read_cache(self, url: str) -> FetchedPage | None:
        body_path, metadata_path = self._paths(url)
        if not body_path.is_file() or not metadata_path.is_file():
            return None
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            body = body_path.read_bytes()
            digest = hashlib.sha256(body).hexdigest()
            if metadata.get("url") != url or metadata.get("sha256") != digest:
                raise FetchError(f"Cached page failed integrity check: {url}")
            return FetchedPage(
                url=url,
                html=body.decode(metadata.get("encoding", "utf-8"), errors="strict"),
                retrieved_at=str(metadata["retrieved_at"]),
                sha256=digest,
                status_code=int(metadata.get("status_code", 200)),
                from_cache=True,
                headers=dict(metadata.get("headers", {})),
            )
        except (OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise FetchError(f"Cached page is incomplete or invalid ({url}): {exc}") from exc

    def _write_cache(self, page: FetchedPage, body: bytes) -> None:
        body_path, metadata_path = self._paths(page.url)
        body_tmp = body_path.with_suffix(".html.tmp")
        metadata_tmp = metadata_path.with_suffix(".json.tmp")
        metadata = {
            "url": page.url,
            "retrieved_at": page.retrieved_at,
            "sha256": page.sha256,
            "status_code": page.status_code,
            "encoding": "utf-8",
            "headers": page.headers,
        }
        body_tmp.write_bytes(body)
        metadata_tmp.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        body_tmp.replace(body_path)
        metadata_tmp.replace(metadata_path)

    def _request(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        expect_html: bool = True,
    ) -> tuple[bytes, dict[str, str], int]:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != TLIDB_HOST:
            raise FetchError(f"Only HTTPS TLIDB pages may be fetched: {url}")
        request_headers = {
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,text/plain;q=0.8,*/*;q=0.3",
        }
        request_headers.update(headers or {})
        last_error: Exception | None = None
        for attempt in range(self.retries + 1):
            self._rate_limit()
            try:
                request = Request(url, headers=request_headers)
                with urlopen(request, timeout=self.timeout) as response:
                    status = int(response.status)
                    content_type = response.headers.get_content_type()
                    if status != 200:
                        raise FetchError(f"Unexpected HTTP status {status} for {url}")
                    if content_type not in {"text/html", "application/xhtml+xml", "text/plain"}:
                        raise FetchError(f"Unexpected content type {content_type} for {url}")
                    body = response.read(MAX_PAGE_BYTES + 1)
                    if len(body) > MAX_PAGE_BYTES:
                        raise FetchError(f"Page exceeds {MAX_PAGE_BYTES} bytes: {url}")
                    if expect_html and b"<html" not in body[:4096].lower() and b"<!doctype html" not in body[:4096].lower():
                        raise FetchError(f"Response does not appear to be an HTML page: {url}")
                    charset = response.headers.get_content_charset() or "utf-8"
                    try:
                        text = body.decode(charset)
                    except (LookupError, UnicodeError) as exc:
                        raise FetchError(f"Could not decode {url} using {charset}: {exc}") from exc
                    normalized = text.encode("utf-8")
                    response_headers = {
                        key.lower(): value
                        for key, value in response.headers.items()
                        if key.lower() in {"etag", "last-modified", "content-type", "cache-control"}
                    }
                    return normalized, response_headers, status
            except HTTPError as exc:
                last_error = exc
                if exc.code not in RETRYABLE_STATUS or attempt >= self.retries:
                    raise FetchError(f"HTTP {exc.code} while fetching {url}") from exc
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                try:
                    wait = min(30.0, max(float(retry_after), 2.0 ** attempt))
                except ValueError:
                    wait = min(30.0, 2.0 ** attempt)
                time.sleep(wait)
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= self.retries:
                    raise FetchError(f"Network error while fetching {url}: {exc}") from exc
                time.sleep(min(30.0, 2.0 ** attempt))
        raise FetchError(f"Fetch failed for {url}: {last_error}")

    def _ensure_robots(self, *, refresh: bool = False) -> RobotFileParser:
        if self._robots is not None and not refresh:
            return self._robots
        cache_path = self.cache_dir / "robots.txt"
        metadata_path = self.cache_dir / "robots.json"
        text: str | None = None
        if not refresh and cache_path.is_file() and metadata_path.is_file():
            try:
                metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
                cached_at = datetime.fromisoformat(metadata["retrieved_at"])
                age = datetime.now(timezone.utc) - cached_at
                if age.total_seconds() < 24 * 60 * 60:
                    text = cache_path.read_text(encoding="utf-8")
                    self._robots_retrieved_at = metadata["retrieved_at"]
            except (OSError, ValueError, KeyError, json.JSONDecodeError):
                text = None
        if text is None:
            if self.offline:
                if not cache_path.is_file():
                    raise FetchError("Offline mode requires a cached TLIDB robots.txt.")
                text = cache_path.read_text(encoding="utf-8")
                self._robots_retrieved_at = "cached-offline"
            else:
                body, _, status = self._request(ROBOTS_URL, expect_html=False)
                if status != 200:
                    raise FetchError(f"Could not read robots.txt (HTTP {status}).")
                text = body.decode("utf-8")
                self._robots_retrieved_at = self._now()
                cache_path.write_text(text, encoding="utf-8")
                metadata_path.write_text(
                    json.dumps({"retrieved_at": self._robots_retrieved_at}, indent=2) + "\n",
                    encoding="utf-8",
                )
        parser = RobotFileParser(ROBOTS_URL)
        parser.parse(text.splitlines())
        self._robots = parser
        return parser

    @property
    def robots_retrieved_at(self) -> str:
        return self._robots_retrieved_at

    def fetch(self, url: str, *, refresh: bool = False) -> FetchedPage:
        parsed = urlparse(url)
        if parsed.scheme != "https" or parsed.hostname != TLIDB_HOST:
            raise FetchError(f"Only HTTPS TLIDB pages may be fetched: {url}")
        if self.offline:
            cached = self._read_cache(url)
            if cached is None:
                raise FetchError(f"No cached copy exists for offline page: {url}")
            return cached
        robots = self._ensure_robots()
        if not robots.can_fetch(USER_AGENT, url):
            raise FetchError(f"robots.txt disallows this page: {url}")
        cached = None if refresh else self._read_cache(url)
        if cached:
            return cached
        body, headers, status = self._request(url)
        try:
            text = body.decode("utf-8")
        except UnicodeError as exc:
            raise FetchError(f"Normalized response is not valid UTF-8: {url}") from exc
        page = FetchedPage(
            url=url,
            html=text,
            retrieved_at=self._now(),
            sha256=hashlib.sha256(body).hexdigest(),
            status_code=status,
            from_cache=False,
            headers=headers,
        )
        self._write_cache(page, body)
        return page
