def test_unauthorized_without_session_header(client):
    response = client.post("/api/conversations", json={"title": "Test Chat"})
    assert response.status_code == 401
    assert "UNAUTHORIZED_SESSION" in response.json()["code"]


def test_unauthorized_with_invalid_session_header(client):
    response = client.post(
        "/api/conversations",
        headers={"X-Session-ID": "invalid-short-token"},
        json={"title": "Test Chat"}
    )
    assert response.status_code == 401


def test_conversation_crud_and_isolation(client, session_id_a, session_id_b):
    headers_a = {"X-Session-ID": session_id_a}
    headers_b = {"X-Session-ID": session_id_b}

    # 1. Session A creates a conversation
    create_res = client.post("/api/conversations", headers=headers_a, json={"title": "Session A Chat"})
    assert create_res.status_code == 201
    conv_a = create_res.json()
    conv_a_id = conv_a["id"]
    assert conv_a["title"] == "Session A Chat"

    # 2. Session A lists conversations
    list_res_a = client.get("/api/conversations", headers=headers_a)
    assert list_res_a.status_code == 200
    assert len(list_res_a.json()["conversations"]) == 1

    # 3. Session B lists conversations -> must be 0 (Isolated!)
    list_res_b = client.get("/api/conversations", headers=headers_b)
    assert list_res_b.status_code == 200
    assert len(list_res_b.json()["conversations"]) == 0

    # 4. Session B tries to access Session A's conversation -> 404 Not Found
    get_b = client.get(f"/api/conversations/{conv_a_id}", headers=headers_b)
    assert get_b.status_code == 404

    # 5. Session A accesses own conversation -> 200 OK
    get_a = client.get(f"/api/conversations/{conv_a_id}", headers=headers_a)
    assert get_a.status_code == 200
    assert get_a.json()["id"] == conv_a_id

    # 6. Session B tries to delete Session A's conversation -> 404 Not Found
    del_b = client.delete(f"/api/conversations/{conv_a_id}", headers=headers_b)
    assert del_b.status_code == 404

    # 7. Session A deletes own conversation -> 204 No Content
    del_a = client.delete(f"/api/conversations/{conv_a_id}", headers=headers_a)
    assert del_a.status_code == 204

    # 8. Verifying deletion
    get_after = client.get(f"/api/conversations/{conv_a_id}", headers=headers_a)
    assert get_after.status_code == 404


def test_feedback_submission(client, session_id_a, session_id_b):
    headers_a = {"X-Session-ID": session_id_a}
    headers_b = {"X-Session-ID": session_id_b}

    # Create conv and chat message for Session A
    conv = client.post("/api/conversations", headers=headers_a, json={}).json()
    chat_res = client.post(
        "/api/chat",
        headers=headers_a,
        json={"conversation_id": conv["id"], "message": "Hello MindBridge!"}
    ).json()

    asst_msg_id = chat_res["assistant_message"]["id"]

    # Session B tries to submit feedback for Session A's message -> 404
    fb_unauth = client.post(
        "/api/feedback",
        headers=headers_b,
        json={"message_id": asst_msg_id, "feedback_type": "helpful"}
    )
    assert fb_unauth.status_code == 404

    # Session A submits feedback -> 201
    fb_auth = client.post(
        "/api/feedback",
        headers=headers_a,
        json={"message_id": asst_msg_id, "feedback_type": "helpful", "comment": "Great answer!"}
    )
    assert fb_auth.status_code == 201
    assert fb_auth.json()["feedback_type"] == "helpful"
