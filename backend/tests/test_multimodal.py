def test_image_inspection_and_multimodal_chat(client, session_id_a, sample_image_png_bytes):
    headers = {"X-Session-ID": session_id_a}
    conv = client.post("/api/conversations", headers=headers, json={}).json()

    # Valid PNG upload with prompt
    res = client.post(
        "/api/chat/multimodal",
        headers=headers,
        data={
            "conversation_id": conv["id"],
            "message": "Can you inspect this chart?",
            "use_rag": "false"
        },
        files={"image_file": ("test_chart.png", sample_image_png_bytes, "image/png")}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["user_message"]["input_modality"] == "image"
    assert data["assistant_message"]["input_modality"] == "image"
    content = data["assistant_message"]["content"]
    assert "PNG" in content or "chart" in content.lower()


def test_reject_fake_image_file(client, session_id_a):
    headers = {"X-Session-ID": session_id_a}
    conv = client.post("/api/conversations", headers=headers, json={}).json()

    # Disguised executable/corrupted bytes declared as image/png
    fake_bytes = b"NOT_A_REAL_IMAGE_FILE_JUST_TEXT"
    res = client.post(
        "/api/chat/multimodal",
        headers=headers,
        data={"conversation_id": conv["id"], "message": "Analyze this"},
        files={"image_file": ("fake.png", fake_bytes, "image/png")}
    )
    assert res.status_code == 400
    assert "Invalid image format" in res.json()["error"]


def test_audio_transcription(client, session_id_a, sample_audio_wav_bytes):
    headers = {"X-Session-ID": session_id_a}

    res = client.post(
        "/api/audio/transcribe",
        headers=headers,
        files={"file": ("recording.wav", sample_audio_wav_bytes, "audio/wav")}
    )
    assert res.status_code == 200
    data = res.json()
    assert "text" in data
    assert len(data["text"]) > 0


def test_reject_corrupted_audio(client, session_id_a):
    headers = {"X-Session-ID": session_id_a}

    res = client.post(
        "/api/audio/transcribe",
        headers=headers,
        files={"file": ("fake.wav", b"INVALID_AUDIO_DATA_HEADER", "audio/wav")}
    )
    assert res.status_code == 400
    assert "audio file signature" in res.json()["error"]


def test_audio_synthesis(client, session_id_a):
    headers = {"X-Session-ID": session_id_a}

    res = client.post(
        "/api/audio/synthesize",
        headers=headers,
        json={"text": "MindBridge AI emotional support assistance."}
    )
    assert res.status_code == 200
    data = res.json()
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 100
    assert data["content_type"] == "audio/wav"
