import json

from backend import db


def approve(client, claim_id="CLM-1001", payout=420.0):
    return client.post(
        f"/api/claims/{claim_id}/decision",
        json={
            "decision": "approve",
            "payout": payout,
            "reason": "Covered.",
            "policy_section": "2",
        },
    )


def test_decline_with_a_payout_is_rejected(client):
    response = client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "decision": "decline",
            "payout": 10,
            "reason": "No.",
            "policy_section": "2",
        },
    )
    assert response.status_code == 409


def test_approval_needs_a_payout_above_zero(client):
    assert approve(client, payout=0).status_code == 409


def test_approval_up_to_the_limit_is_approved(client):
    response = approve(client, payout=1000.00)
    assert response.json()["state"] == "approved"
    assert response.json()["payout"] == 1000.00


def test_approval_over_the_limit_waits_for_sign_off(client):
    response = approve(client, payout=1000.01)
    assert response.json()["state"] == "waiting_for_sign_off"
    assert response.json()["decision"] == "approve"


def test_refer_means_docs_missing(client):
    response = client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "decision": "refer",
            "payout": 0,
            "reason": "Needs more.",
            "policy_section": "9",
        },
    )
    assert response.json()["state"] == "docs_missing"


def test_decision_on_a_finished_claim_is_rejected(client):
    approve(client)
    assert approve(client).status_code == 409


def test_decision_on_an_unknown_claim_is_not_found(client):
    assert approve(client, claim_id="CLM-0000").status_code == 404


def test_payment_before_sign_off_is_blocked(client):
    approve(client, payout=1250.00)
    response = client.post("/api/claims/CLM-1001/payments", json={"amount": 1250.00})
    assert response.status_code == 409
    assert client.get("/api/claims/CLM-1001").json()["payments"] == []


def test_sign_off_then_payment(client):
    approve(client, payout=1250.00)
    signed = client.post("/api/claims/CLM-1001/sign-off", json={"handler_id": "HND-01"})
    assert signed.json()["state"] == "approved"
    assert signed.json()["signed_off_by"] == "HND-01"

    paid = client.post("/api/claims/CLM-1001/payments", json={"amount": 1250.00})
    assert paid.status_code == 200
    assert [payment["amount"] for payment in paid.json()["payments"]] == [1250.00]

    again = client.post("/api/claims/CLM-1001/payments", json={"amount": 1250.00})
    assert again.status_code == 409


def test_payment_must_match_the_approved_payout(client):
    approve(client, payout=420.00)
    response = client.post("/api/claims/CLM-1001/payments", json={"amount": 500.00})
    assert response.status_code == 409
    assert response.json()["detail"] == "The approved payout is $420.00"


def test_payment_of_a_claim_not_approved_is_blocked(client):
    response = client.post("/api/claims/CLM-1001/payments", json={"amount": 420.00})
    assert response.status_code == 409
    client.post(
        "/api/claims/CLM-1001/decision",
        json={
            "decision": "decline",
            "payout": 0,
            "reason": "No.",
            "policy_section": "2",
        },
    )
    response = client.post("/api/claims/CLM-1001/payments", json={"amount": 0})
    assert response.status_code == 409


def test_payment_of_a_claim_not_yet_approved_is_blocked(client):
    response = client.post("/api/claims/CLM-1001/payments", json={"amount": 420.00})
    assert response.status_code == 409


def test_sign_off_needs_a_claim_waiting_for_it(client):
    response = client.post(
        "/api/claims/CLM-1001/sign-off", json={"handler_id": "HND-01"}
    )
    assert response.status_code == 409


def test_sign_off_needs_a_handler_with_authority(client):
    with db.connection() as conn:
        record = json.loads(
            conn.execute("SELECT record FROM handlers WHERE id = 'HND-02'").fetchone()[
                0
            ]
        )
        record["can_approve_over_limit"] = False
        conn.execute(
            "UPDATE handlers SET record = ? WHERE id = 'HND-02'", (json.dumps(record),)
        )
    approve(client, payout=1250.00)
    response = client.post(
        "/api/claims/CLM-1001/sign-off", json={"handler_id": "HND-02"}
    )
    assert response.status_code == 409


def test_unknown_handler_is_not_found(client):
    approve(client, payout=1250.00)
    response = client.post(
        "/api/claims/CLM-1001/sign-off", json={"handler_id": "HND-99"}
    )
    assert response.status_code == 404


def test_steps_are_logged_in_order(client):
    for tool in ["get_claim", "get_policy_wording"]:
        response = client.post(
            "/api/claims/CLM-1001/steps",
            json={"tool": tool, "input": "{}", "output": "ok"},
        )
        assert response.json() == {"status": "recorded"}
    steps = client.get("/api/claims/CLM-1001").json()["steps"]
    assert [step["tool"] for step in steps] == ["get_claim", "get_policy_wording"]


def test_step_on_an_unknown_claim_is_not_found(client):
    response = client.post(
        "/api/claims/CLM-0000/steps", json={"tool": "x", "input": "", "output": ""}
    )
    assert response.status_code == 404


def test_handlers_are_listed(client):
    handlers = client.get("/api/handlers").json()
    assert [handler["handler_id"] for handler in handlers] == [
        "HND-01",
        "HND-02",
        "HND-03",
    ]
    assert "email" not in handlers[0]


def test_claim_shows_the_decision_and_its_reasons(client):
    approve(client, payout=420.00)
    client.post(
        "/api/claims/CLM-1001/steps",
        json={"tool": "record_decision", "input": "{}", "output": "ok"},
    )
    claim = client.get("/api/claims/CLM-1001").json()
    assert claim["decision"] == "approve"
    assert claim["payout"] == 420.00
    assert claim["reason"] == "Covered."
    assert claim["policy_section"] == "2"
    assert [step["tool"] for step in claim["steps"]] == ["record_decision"]
