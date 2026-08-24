from tests.conftest import register_and_login, make_admin


def _create_complaint(client, token, category="Plumbing", description="Leaking pipe under the kitchen sink for two days now."):
    return client.post(
        "/complaints",
        data={"category": category, "description": description},
        headers={"Authorization": f"Bearer {token}"},
    )


def test_resident_can_create_and_view_own_complaint(client):
    token = register_and_login(client)
    resp = _create_complaint(client, token)
    assert resp.status_code == 201
    body = resp.json()
    assert body["status"] == "OPEN"
    assert body["priority"] == "MEDIUM"
    assert body["reference_code"].startswith("SMT-")
    assert len(body["history"]) == 1
    assert body["history"][0]["event_type"] == "CREATED"

    complaint_id = body["id"]
    get_resp = client.get(f"/complaints/{complaint_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_resp.status_code == 200


def test_resident_cannot_access_other_residents_complaint(client):
    token_a = register_and_login(client, email="a@test.dev", name="Resident A")
    complaint_id = _create_complaint(client, token_a).json()["id"]

    token_b = register_and_login(client, email="b@test.dev", name="Resident B")
    resp = client.get(f"/complaints/{complaint_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert resp.status_code == 404  # not 403, to avoid leaking existence


def test_resident_cannot_access_admin_endpoints(client):
    token = register_and_login(client)
    resp = client.get("/admin/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_admin_can_update_status_and_history_is_recorded(client):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]
    admin_token = make_admin(client, None)

    resp = client.patch(
        f"/complaints/{complaint_id}/status",
        json={"status": "IN_PROGRESS", "note": "Plumber assigned."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "IN_PROGRESS"
    assert len(body["history"]) == 2
    assert body["history"][-1]["previous_status"] == "OPEN"
    assert body["history"][-1]["new_status"] == "IN_PROGRESS"


def test_invalid_status_transition_rejected(client):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]
    admin_token = make_admin(client, None)

    # OPEN -> RESOLVED is allowed; RESOLVED -> IN_PROGRESS is not (terminal state).
    client.patch(f"/complaints/{complaint_id}/status", json={"status": "RESOLVED"},
                 headers={"Authorization": f"Bearer {admin_token}"})
    resp = client.patch(f"/complaints/{complaint_id}/status", json={"status": "IN_PROGRESS"},
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400


def test_resolved_complaint_requires_reopen_endpoint(client):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]
    admin_token = make_admin(client, None)

    client.patch(f"/complaints/{complaint_id}/status", json={"status": "RESOLVED"},
                 headers={"Authorization": f"Bearer {admin_token}"})

    # Reopen without a note should fail
    resp = client.patch(f"/complaints/{complaint_id}/reopen", json={"status": "OPEN"},
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 400

    resp = client.patch(f"/complaints/{complaint_id}/reopen", json={"status": "OPEN", "note": "Issue recurred."},
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "OPEN"


def test_priority_update_recorded_in_history(client):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]
    admin_token = make_admin(client, None)

    resp = client.patch(f"/complaints/{complaint_id}/priority", json={"priority": "HIGH", "note": "Escalated."},
                         headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "HIGH"
    assert resp.json()["history"][-1]["event_type"] == "PRIORITY_CHANGE"


def test_overdue_detection(client, monkeypatch):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]

    from app.database import SessionLocal
    from app.models import Complaint
    from datetime import datetime, timedelta

    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    c.created_at = datetime.utcnow() - timedelta(days=10)
    db.commit()
    db.close()

    admin_token = make_admin(client, None)
    resp = client.get("/admin/complaints?overdue_only=true", headers={"Authorization": f"Bearer {admin_token}"})
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert complaint_id in ids


def test_resolved_complaint_not_overdue(client):
    resident_token = register_and_login(client)
    complaint_id = _create_complaint(client, resident_token).json()["id"]

    from app.database import SessionLocal
    from app.models import Complaint, ComplaintStatus
    from datetime import datetime, timedelta

    db = SessionLocal()
    c = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    c.created_at = datetime.utcnow() - timedelta(days=10)
    c.status = ComplaintStatus.RESOLVED
    db.commit()
    db.close()

    admin_token = make_admin(client, None)
    resp = client.get("/admin/complaints?overdue_only=true", headers={"Authorization": f"Bearer {admin_token}"})
    ids = [c["id"] for c in resp.json()]
    assert complaint_id not in ids


def test_empty_complaint_list(client):
    token = register_and_login(client)
    resp = client.get("/complaints", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []


def test_invalid_photo_type_rejected(client):
    token = register_and_login(client)
    resp = client.post(
        "/complaints",
        data={"category": "Plumbing", "description": "Leaking pipe under the kitchen sink."},
        files={"photo": ("note.txt", b"not an image", "text/plain")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400
