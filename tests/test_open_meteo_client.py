from __future__ import annotations

from solarstorm.open_meteo._client import (
    OpenMeteoResponse,
    build_request_url,
    hash_text,
)


def test_build_request_url_is_stable_and_sorted():
    url = build_request_url(
        "https://example.test/forecast",
        {"longitude": 174.8053, "latitude": -41.3272, "hourly": "temperature_2m"},
    )

    assert url == (
        "https://example.test/forecast?"
        "hourly=temperature_2m&latitude=-41.3272&longitude=174.8053"
    )


def test_open_meteo_response_hashes_request_and_body():
    response = OpenMeteoResponse.from_text(
        request_url="https://example.test/forecast?latitude=-41.3272",
        status_code=200,
        text='{"hourly":{"temperature_2m":[12.3]}}',
    )

    assert response.ok is True
    assert response.request_url_sha256 == hash_text(response.request_url)
    assert response.response_sha256 == hash_text(response.text)
