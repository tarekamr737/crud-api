from dataclasses import dataclass

import pytest

from src.fetcher import DEFAULT_TIMEOUT, FetchError, fetch_http


@dataclass
class FakeResponse:
    status_code: int
    text: str = "<html>ok</html>"


class FakeSession:
    def __init__(self, response: FakeResponse) -> None:
        self.response = response
        self.calls: list[tuple[str, dict[str, str], float]] = []

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> FakeResponse:
        self.calls.append((url, headers, timeout))
        return self.response


def test_fetch_http_is_identifiable_timed_and_delayed() -> None:
    session = FakeSession(FakeResponse(200))
    delays: list[float] = []

    html = fetch_http("https://example.test/page", session=session, sleep=delays.append)

    assert html == "<html>ok</html>"
    assert delays == [0.5]
    assert len(session.calls) == 1
    url, headers, timeout = session.calls[0]
    assert url == "https://example.test/page"
    assert "ThePoliteScraper" in headers["User-Agent"]
    assert "contact:" in headers["User-Agent"]
    assert timeout == DEFAULT_TIMEOUT


def test_fetch_http_rejects_non_200_before_returning_html() -> None:
    session = FakeSession(FakeResponse(404, "should not be parsed"))

    with pytest.raises(FetchError, match=r"example\.test/missing: HTTP 404"):
        fetch_http(
            "https://example.test/missing",
            session=session,
            sleep=lambda _: None,
        )
