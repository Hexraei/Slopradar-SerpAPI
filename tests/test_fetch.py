import requests
import pytest
from slopradar.fetch import PageFetcher, MAX_BYTES


class Response:
    status_code = 200
    headers = {"Content-Type": "text/html"}
    encoding = "utf-8"
    url = "https://example.com/story"
    closed = False

    def __init__(self, chunks):
        self.chunks = chunks

    def iter_content(self, size):
        for chunk in self.chunks:
            if isinstance(chunk, Exception):
                raise chunk
            yield chunk

    def close(self):
        self.closed = True


class Session:
    headers = {}

    def __init__(self, response):
        self.response = response

    def get(self, *args, **kwargs):
        return self.response


@pytest.mark.parametrize("chunks,error", [
    ([b"<p>partial", requests.exceptions.ChunkedEncodingError("broken")], "download failed"),
    ([b"x" * (MAX_BYTES + 1)], "byte limit"),
])
def test_failed_or_oversized_download_is_unscored_and_closed(chunks, error):
    response = Response(chunks)
    page = PageFetcher(session=Session(response), respect_robots=False).fetch(response.url)
    assert not page.ok and error in page.error and response.closed
    assert not page.html


def test_complete_download_is_closed_and_retains_redirect():
    response = Response([b"<p>Story</p>"])
    page = PageFetcher(session=Session(response), respect_robots=False).fetch("https://example.com/start")
    assert page.ok and page.html == "<p>Story</p>" and response.closed
    assert page.final_url == response.url
