import os
import sys
import tempfile

os.environ["DATABASE_URL"] = "sqlite:///./test_societyhub.db"
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp()
os.environ["JWT_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, engine
from app.main import app


@pytest.fixture(autouse=True)
def _reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)


def register_and_login(client, email="resident@test.dev", name="Test Resident", password="TestPass123!"):
    client.post("/auth/register", json={"name": name, "email": email, "password": password, "flat_number": "A-1"})
    resp = client.post("/auth/login", json={"email": email, "password": password})
    return resp.json()["access_token"]


def make_admin(client, db_session_factory):
    """Register a user then promote to admin directly via DB (no public admin-signup endpoint by design)."""
    from app.database import SessionLocal
    from app.models import User, UserRole
    client.post("/auth/register", json={"name": "Admin User", "email": "admin@test.dev", "password": "AdminPass123!"})
    db = SessionLocal()
    user = db.query(User).filter(User.email == "admin@test.dev").first()
    user.role = UserRole.ADMIN
    db.commit()
    db.close()
    resp = client.post("/auth/login", json={"email": "admin@test.dev", "password": "AdminPass123!"})
    return resp.json()["access_token"]
