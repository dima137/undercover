import shutil

from fastapi.routing import APIRoute

from backend import db
from backend.main import app


def test_queue_has_25_waiting_claims(client):
    claims = client.get("/api/claims").json()
    assert len(claims) == 25
    assert {claim["state"] for claim in claims} == {"waiting"}


def test_claim_in_full(client):
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["policy"]["policy_id"] == "POL-2001"
    assert claim["plan"]["plan"] == "premium"
    assert claim["customer"]["customer_id"] == "CUS-3001"
    assert claim["decision"] is None
    assert claim["payments"] == []


def test_unknown_claim_is_not_found(client):
    assert client.get("/api/claims/CLM-0000").status_code == 404


def test_policy_wording_and_instructions(client):
    assert client.get("/api/policy-wording").json()["text"].startswith("# UnderCover")
    assert "UnderCover Agent" in client.get("/api/instructions").json()["text"]


def test_loader_reads_only_the_pilot_files(tmp_path, monkeypatch):
    for name in ["claims", "policies", "customers", "plans", "handlers", "company"]:
        shutil.copy(db.DATA_DIR / f"{name}.json", tmp_path)
    shutil.copy(db.DATA_DIR / "policy_wording.md", tmp_path)
    monkeypatch.setattr(db, "DATA_DIR", tmp_path)
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "undercover.db")
    db.reset()
    with db.connection() as conn:
        for sql, count in [
            ("SELECT COUNT(*) FROM claims", 25),
            ("SELECT COUNT(*) FROM policies", 50),
            ("SELECT COUNT(*) FROM customers", 49),
            ("SELECT COUNT(*) FROM plans", 3),
            ("SELECT COUNT(*) FROM handlers", 3),
        ]:
            assert conn.execute(sql).fetchone()[0] == count


def test_every_operation_has_an_id_a_one_line_docstring_and_no_optional_inputs():
    spec = app.openapi()
    api_routes = [route for route in app.routes if isinstance(route, APIRoute)]
    for route in api_routes:
        if not route.path.startswith("/api"):
            continue
        assert route.endpoint.__doc__
        assert "\n" not in route.endpoint.__doc__.strip()
    for path, methods in spec["paths"].items():
        for operation in methods.values():
            assert operation["operationId"], path
            for parameter in operation.get("parameters", []):
                assert parameter["required"], (path, parameter["name"])
            if "requestBody" in operation:
                ref = operation["requestBody"]["content"]["application/json"]["schema"][
                    "$ref"
                ]
                body = spec["components"]["schemas"][ref.rsplit("/", 1)[1]]
                assert set(body.get("properties", {})) == set(
                    body.get("required", [])
                ), path
