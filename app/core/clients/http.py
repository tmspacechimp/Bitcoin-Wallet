from dataclasses import dataclass, field
from typing import Any, Dict, List, Protocol

from fastapi import HTTPException
from requests import get


class IHTTPClient(Protocol):
    def get(self, url: str) -> Dict[str, Any] | List[Any]:
        pass


@dataclass
class RequestsClient(IHTTPClient):
    timeout_s: int = 5
    headers: dict[str, str] = field(default_factory=dict)

    def get(self, url: str) -> Dict[str, Any] | List[Any]:
        response = get(url, timeout=self.timeout_s, headers=self.headers)
        try:
            response.raise_for_status()
        except Exception:
            raise HTTPException(status_code=500, detail="Service Unavailable")
        return response.json()  # type: ignore


@dataclass
class RequestsClientBuilder:
    _timeout_s: int = field(init=False, default=5)
    _headers: dict[str, str] = field(init=False, default_factory=dict)

    def with_timeout(self, seconds: int) -> "RequestsClientBuilder":
        self._timeout_s = seconds

        return self

    def with_header(self, name: str, value: str) -> "RequestsClientBuilder":
        self._headers[name] = value

        return self

    def build(self) -> RequestsClient:
        return RequestsClient(self._timeout_s, self._headers)
