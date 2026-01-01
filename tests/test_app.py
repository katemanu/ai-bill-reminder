import pytest
from app import create_app
from app.models import db, User, Bill


@pytest.fixture
def app():
    """Create test application."""
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """Register user and return auth headers."""
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123",
        "name": "Test User"
    })
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestHealth:
    """Health endpoint tests."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"


class TestAuth:
    """Authentication tests."""

    def test_register_success(self, client):
        response = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "Password123",
            "name": "New User"
        })
        assert response.status_code == 201
        data = response.get_json()
        assert "access_token" in data
        assert data["user"]["email"] == "new@example.com"

    def test_register_duplicate_email(self, client):
        client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "Password123",
            "name": "User"
        })
        response = client.post("/api/auth/register", json={
            "email": "dup@example.com",
            "password": "Password123",
            "name": "User"
        })
        assert response.status_code == 409

    def test_login_success(self, client):
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "Password123",
            "name": "User"
        })
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "Password123"
        })
        assert response.status_code == 200
        assert "access_token" in response.get_json()

    def test_login_wrong_password(self, client):
        client.post("/api/auth/register", json={
            "email": "wrong@example.com",
            "password": "Password123",
            "name": "User"
        })
        response = client.post("/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "WrongPass"
        })
        assert response.status_code == 401

    def test_get_current_user(self, client, auth_headers):
        response = client.get("/api/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["user"]["email"] == "test@example.com"


class TestBills:
    """Bill management tests."""

    def test_create_bill(self, client, auth_headers):
        response = client.post("/api/bills", headers=auth_headers, json={
            "name": "Test Bill",
            "amount": 100.00,
            "due_date": "2026-01-15",
            "frequency": "monthly",
            "category": "utilities"
        })
        assert response.status_code == 201
        assert response.get_json()["bill"]["name"] == "Test Bill"

    def test_list_bills(self, client, auth_headers):
        client.post("/api/bills", headers=auth_headers, json={
            "name": "Bill 1",
            "amount": 50.00,
            "due_date": "2026-01-10"
        })
        response = client.get("/api/bills", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["count"] >= 1

    def test_get_bill(self, client, auth_headers):
        create_resp = client.post("/api/bills", headers=auth_headers, json={
            "name": "Get Bill",
            "amount": 75.00,
            "due_date": "2026-02-01"
        })
        bill_id = create_resp.get_json()["bill"]["id"]
        response = client.get(f"/api/bills/{bill_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.get_json()["bill"]["name"] == "Get Bill"

    def test_update_bill(self, client, auth_headers):
        create_resp = client.post("/api/bills", headers=auth_headers, json={
            "name": "Update Bill",
            "amount": 100.00,
            "due_date": "2026-01-20"
        })
        bill_id = create_resp.get_json()["bill"]["id"]
        response = client.put(f"/api/bills/{bill_id}", headers=auth_headers, json={
            "amount": 150.00,
            "is_paid": True
        })
        assert response.status_code == 200
        assert response.get_json()["bill"]["amount"] == 150.00

    def test_delete_bill(self, client, auth_headers):
        create_resp = client.post("/api/bills", headers=auth_headers, json={
            "name": "Delete Bill",
            "amount": 25.00,
            "due_date": "2026-03-01"
        })
        bill_id = create_resp.get_json()["bill"]["id"]
        response = client.delete(f"/api/bills/{bill_id}", headers=auth_headers)
        assert response.status_code == 200

    def test_unauthorized_access(self, client):
        response = client.get("/api/bills")
        assert response.status_code == 401
