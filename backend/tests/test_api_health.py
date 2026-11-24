def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["service"] == "MindBridge AI"
    assert "providers" in data
    assert data["providers"]["llm"] in ["mock", "gemini", "openai"]


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "api_documentation" in data
    assert "frontend_ui" in data


def test_session_generation(client):
    response = client.get("/api/session/new")
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    session_id = data["session_id"]
    # Check 64-character hex format
    assert len(session_id) == 64
    int(session_id, 16)  # Verifies hex decodability
