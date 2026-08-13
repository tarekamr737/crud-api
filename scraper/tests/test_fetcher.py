from dataclasses import dataclass

import pytest
import requests

from src.fetcher import DEFAULT_TIMEOUT, FetchError, FetchStats, fetch, fetch_http


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


def test_fetch_then_cache_hit_avoids_a_second_request(tmp_path, capsys) -> None:
    calls: list[str] = []
    stats = FetchStats()

    def fake_http_fetch(url: str) -> str:
        calls.append(url)
        return "<html>cached</html>"

    url = "https://example.test/catalogue/page-1.html"
    first = fetch(url, cache_dir=tmp_path, stats=stats, http_fetch=fake_http_fetch)
    second = fetch(url, cache_dir=tmp_path, stats=stats, http_fetch=fake_http_fetch)

    assert first == second == "<html>cached</html>"
    assert calls == [url]
    assert stats.pages_fetched == 1
    assert stats.cache_hits == 1
    assert len(list(tmp_path.glob("*.html"))) == 1
    assert capsys.readouterr().out.splitlines() == [f"FETCH {url}", f"CACHE HIT {url}"]


class SequenceSession:
    def __init__(self, outcomes: list[FakeResponse | Exception]) -> None:
        self.outcomes = outcomes
        self.calls = 0

    def get(self, url: str, *, headers: dict[str, str], timeout: float) -> FakeResponse:
        outcome = self.outcomes[self.calls]
        self.calls += 1
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def test_5xx_retries_once_then_succeeds() -> None:
    session = SequenceSession([FakeResponse(503), FakeResponse(200, "recovered")])
    delays: list[float] = []

    assert fetch_http("https://example.test", session=session, sleep=delays.append) == "recovered"
    assert session.calls == 2
    assert delays == [0.5, 0.5]


def test_timeout_retries_once_then_succeeds() -> None:
    session = SequenceSession([requests.Timeout("slow"), FakeResponse(200, "recovered")])

    assert (
        fetch_http("https://example.test", session=session, sleep=lambda _: None)
        == "recovered"
    )
    assert session.calls == 2


def test_5xx_fails_after_exactly_one_retry() -> None:
    session = SequenceSession([FakeResponse(500), FakeResponse(502)])

    with pytest.raises(FetchError, match="HTTP 502"):
        fetch_http("https://example.test", session=session, sleep=lambda _: None)

    assert session.calls == 2


@pytest.mark.parametrize("status_code", [403, 404])
def test_403_and_404_are_never_retried(status_code: int) -> None:
    session = SequenceSession([FakeResponse(status_code), FakeResponse(200)])

    with pytest.raises(FetchError, match=rf"HTTP {status_code}"):
        fetch_http("https://example.test", session=session, sleep=lambda _: None)

    assert session.calls == 1
