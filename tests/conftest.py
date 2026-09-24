import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def serp_payload():
    return json.loads((FIXTURES / "serp_google.json").read_text(encoding="utf-8"))


@pytest.fixture
def slop_html():
    return (FIXTURES / "slop_page.html").read_text(encoding="utf-8")


@pytest.fixture
def human_html():
    return (FIXTURES / "human_page.html").read_text(encoding="utf-8")
