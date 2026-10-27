import pytest
from fastapi.testclient import TestClient

from backend import db
from backend.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "undercover.db")
    with TestClient(app) as test_client:
        yield test_client
