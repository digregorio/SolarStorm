from __future__ import annotations

import hashlib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_request_url(base_url: str, params: dict[str, Any]) -> str:
    query_params = [
        (key, str(value))
        for key, value in sorted(params.items())
        if value is not None
    ]
    query = urllib.parse.urlencode(query_params)
    if not query:
        return base_url
    return f"{base_url}?{query}"


@dataclass(frozen=True)
class OpenMeteoResponse:
    request_url: str
    status_code: int
    text: str
    request_url_sha256: str
    response_sha256: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    @classmethod
    def from_text(
        cls,
        *,
        request_url: str,
        status_code: int,
        text: str,
    ) -> OpenMeteoResponse:
        return cls(
            request_url=request_url,
            status_code=status_code,
            text=text,
            request_url_sha256=hash_text(request_url),
            response_sha256=hash_text(text),
        )


class OpenMeteoClient:
    def __init__(
        self,
        *,
        user_agent: str = "solarstorm-open-meteo/0.1",
        timeout_s: float = 30.0,
    ) -> None:
        self.user_agent = user_agent
        self.timeout_s = timeout_s

    def get(self, base_url: str, params: dict[str, Any]) -> OpenMeteoResponse:
        request_url = build_request_url(base_url, params)
        request = urllib.request.Request(
            request_url,
            headers={"User-Agent": self.user_agent},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                text = response.read().decode("utf-8", errors="replace")
                status_code = int(response.status)
        except urllib.error.HTTPError as error:
            text = error.read().decode("utf-8", errors="replace")
            status_code = int(error.code)

        return OpenMeteoResponse.from_text(
            request_url=request_url,
            status_code=status_code,
            text=text,
        )
