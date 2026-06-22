import sys
from unittest.mock import MagicMock

import pytest

# Mock the entire crews package and its submodules to avoid
# CrewAI Agent validation and missing tool dependencies at import time.
_mock_registry = {
    "match_prep": lambda **kw: {"status": "mocked"},
    "enrollment": lambda **kw: {"status": "mocked"},
    "progress_review": lambda **kw: {"status": "mocked"},
    "season_plan": lambda **kw: {"status": "mocked"},
    "injury_response": lambda **kw: {"status": "mocked"},
}

crews_mock = MagicMock()
crews_mock.CREW_REGISTRY = _mock_registry

sys.modules["crews"] = crews_mock
sys.modules["crews.match_prep"] = MagicMock()
sys.modules["crews.enrollment"] = MagicMock()
sys.modules["crews.progress_review"] = MagicMock()
sys.modules["crews.season_plan"] = MagicMock()
sys.modules["crews.injury_response"] = MagicMock()

from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)
