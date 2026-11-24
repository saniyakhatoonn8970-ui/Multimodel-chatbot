import io
import pymupdf as fitz
from PIL import Image
import wave
import struct
import math
import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from backend.app.core.security import generate_session_id
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import app

# In-memory SQLite database specifically for test isolation using StaticPool
TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables for each test function and teardown afterwards."""
    Base.metadata.create_all(bind=engine_test)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine_test)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def session_id_a():
    return generate_session_id()


@pytest.fixture
def session_id_b():
    return generate_session_id()


@pytest.fixture
def sample_pdf_bytes():
    """Generate a clean, valid 2-page in-memory PDF using PyMuPDF."""
    doc = fitz.open()
    
    # Page 1
    page1 = doc.new_page()
    page1.insert_text(
        (50, 72),
        "MindBridge Documentation Page 1.\n"
        "Cognitive Behavioral Therapy (CBT) helps identify cognitive distortions.\n"
        "Deep breathing exercises activate the parasympathetic nervous system."
    )
    
    # Page 2
    page2 = doc.new_page()
    page2.insert_text(
        (50, 72),
        "MindBridge Documentation Page 2.\n"
        "Sleep hygiene recommends limiting blue light exposure 60 minutes before bedtime.\n"
        "Regular physical exercise supports neuroplasticity and emotional resilience."
    )
    
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


@pytest.fixture
def sample_image_png_bytes():
    """Generate a valid 100x100 PNG in-memory."""
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(73, 109, 137))
    img.save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def sample_audio_wav_bytes():
    """Generate a valid 1-second WAV audio file in-memory."""
    buf = io.BytesIO()
    sample_rate = 16000
    with wave.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        raw_data = bytearray()
        for i in range(sample_rate):
            t = i / sample_rate
            val = int(0.2 * math.sin(2 * math.pi * 440 * t) * 32767)
            raw_data.extend(struct.pack("<h", val))
        wav_file.writeframes(raw_data)
    return buf.getvalue()
