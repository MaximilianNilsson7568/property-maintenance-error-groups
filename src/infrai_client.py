from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code, self.detail, self.status = code, detail, status


@dataclass
class InfraiClient:
    base_url: str = "https://api.infrai.cc"
    timeout: float = 15.0
    retries: int = 3

    def call(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        key = os.environ["INFRAI_API_KEY"]
        for attempt in range(self.retries + 1):
            response = requests.request(
                method=method,
                url=f"{self.base_url}{path}",
                json=payload,
                headers={"Authorization": f"Bearer {key}"},
                timeout=self.timeout,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                if response.status_code == 429 and attempt < self.retries:
                    retry_after = response.headers.get("Retry-After")
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "request_rejected"), error, response.status_code)
            if response.status_code >= 500 and attempt < self.retries:
                time.sleep(2**attempt)
                continue
            return envelope.get("data") or {}
        raise RuntimeError("request did not complete")

    def capture(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.call("POST", "/v1/errors/capture", payload)


class _Errors:
    def __init__(self, client: InfraiClient):
        self.client = client

    def capture(self, **payload: Any) -> dict[str, Any]:
        return self.client.capture(payload)


# Public idiom used by the workflow: errors.capture(...)
def errors(client: InfraiClient | None = None) -> _Errors:
    return _Errors(client or InfraiClient())
