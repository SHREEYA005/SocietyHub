from tests.conftest import register_and_login, make_admin


def test_only_admin_can_create_notice(client):
    token = register_and_login(client)
    resp = client.post("/notices", json={"title": "Test", "content": "Some content", "is_important": False},
                        headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_important_notice_pinned_to_top(client):
    admin_token = make_admin(client, None)
    client.post("/notices", json={"title": "Normal notice", "content": "Regular update.", "is_important": False},
                headers={"Authorization": f"Bearer {admin_token}"})
    client.post("/notices", json={"title": "Important notice", "content": "Urgent update.", "is_important": True},
                headers={"Authorization": f"Bearer {admin_token}"})

    resident_token = register_and_login(client)
    resp = client.get("/notices", headers={"Authorization": f"Bearer {resident_token}"})
    assert resp.status_code == 200
    notices = resp.json()
    assert notices[0]["is_important"] is True


def test_empty_notice_list(client):
    token = register_and_login(client)
    resp = client.get("/notices", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json() == []
