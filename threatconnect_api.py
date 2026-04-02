import base64
import hashlib
import hmac
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode, urlparse

import requests


class ThreatConnectAPIError(RuntimeError):
    pass


@dataclass(frozen=True)
class _AuthHeaders:
    timestamp: str
    authorization: str


class ThreatConnectAPI:
    def __init__(
        self,
        base_url: str,
        access_id: str,
        secret_key: str,
        *,
        timeout: float = 30.0,
        trust_env: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._access_id = access_id
        self._secret_key = secret_key
        self._timeout = timeout
        self._session = session or requests.Session()
        self._session.trust_env = trust_env

        parsed = urlparse(self._base_url)
        self._base_path_prefix = (parsed.path or "").rstrip("/")  # e.g. "/api"

    def _build_auth_headers(self, method: str, path_and_query: str, timestamp: str) -> _AuthHeaders:
        if not path_and_query.startswith("/"):
            raise ValueError("path_and_query must start with '/' (e.g. '/v2/owners')")

        # Docs example signs "/api/v2/...:METHOD:TIMESTAMP" (i.e., includes the base path prefix).
        canonical_path = f"{self._base_path_prefix}{path_and_query}"
        string_to_sign = f"{canonical_path}:{method.upper()}:{timestamp}"

        digest = hmac.new(
            self._secret_key.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        authorization = f"TC {self._access_id}:{signature}"
        return _AuthHeaders(timestamp=timestamp, authorization=authorization)

    def get(self, path: str, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not path.startswith("/"):
            raise ValueError("path must start with '/' (e.g. '/v3/indicators')")

        query = urlencode(params or {}, doseq=True)
        path_and_query = f"{path}?{query}" if query else path

        timestamp = str(int(time.time()))
        auth = self._build_auth_headers("GET", path_and_query, timestamp)

        url = f"{self._base_url}{path_and_query}"
        resp = self._session.get(
            url,
            headers={
                "Timestamp": auth.timestamp,
                "Authorization": auth.authorization,
                "Accept": "application/json",
            },
            timeout=self._timeout,
        )

        try:
            payload = resp.json()
        except Exception:
            payload = None

        if not resp.ok:
            body = resp.text.strip()
            raise ThreatConnectAPIError(
                f"ThreatConnect API request failed: {resp.status_code} {resp.reason}. "
                f"URL={url}. Body={(body[:2000] + '…') if len(body) > 2000 else body}"
            )

        if isinstance(payload, dict):
            return payload
        raise ThreatConnectAPIError(f"Unexpected response JSON type: {type(payload).__name__}")

    def get_owners(self) -> dict[str, Any]:
        return self.get("/v2/owners")

    def get_indicators(self, all: bool = False, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not all: 
            return self.get("/v3/indicators", params=params)

    def get_groups(self, all: bool = False, *, params: dict[str, str] | None = None) -> dict[str, Any]:
        if not all: 
            return self.get("/v3/groups", params=params)
