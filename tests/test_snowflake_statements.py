"""
Tests for Snowflake-compatible statement API endpoints.

These tests verify that the endpoint stubs:
- Return HTTP 501 (Not Implemented) status
- Validate request payloads using Pydantic models
- Return response bodies with the correct structure
"""

from starlette.testclient import TestClient

from data.main import app

client = TestClient(app)


class TestStatementEndpoints:
    """Test suite for Snowflake statement API endpoints."""

    def test_create_statement_returns_501(self):
        """Test POST /api/v2/statements returns 501 Not Implemented."""
        response = client.post(
            "/api/v2/statements",
            json={
                "sqlText": "SELECT * FROM test_table",
                "describeOnly": False,
            },
        )

        assert response.status_code == 501
        data = response.json()

        # Verify response structure
        assert "statementHandle" in data
        assert "status" in data
        assert "created_at" in data

        # Verify status structure
        assert data["status"]["state"] == "NOT_IMPLEMENTED"
        assert "description" in data["status"]

    def test_create_statement_validates_request(self):
        """Test POST /api/v2/statements validates request body."""
        # Missing required field 'sqlText'
        response = client.post("/api/v2/statements", json={})

        assert response.status_code == 422  # Unprocessable Entity (validation error)

    def test_create_statement_with_all_fields(self):
        """Test POST /api/v2/statements with all optional fields."""
        response = client.post(
            "/api/v2/statements",
            json={
                "sqlText": "SELECT * FROM test WHERE id = :id",
                "describeOnly": True,
                "bindValues": {"id": 123},
                "parameters": {"timeout": 30},
            },
        )

        assert response.status_code == 501
        data = response.json()
        assert "statementHandle" in data

    def test_get_statement_status_returns_501(self):
        """Test GET /api/v2/statements/{handle} returns 501 Not Implemented."""
        statement_handle = "test-handle-123"
        response = client.get(f"/api/v2/statements/{statement_handle}")

        assert response.status_code == 501
        data = response.json()

        # Verify response structure
        assert data["statementHandle"] == statement_handle
        assert "status" in data
        assert "progress" in data
        assert "started_at" in data
        assert "finished_at" in data

        # Verify status structure
        assert data["status"]["state"] == "NOT_IMPLEMENTED"

    def test_cancel_statement_returns_501(self):
        """Test POST /api/v2/statements/{handle}/cancel returns 501 Not Implemented."""
        statement_handle = "test-handle-456"
        response = client.post(f"/api/v2/statements/{statement_handle}/cancel")

        assert response.status_code == 501
        data = response.json()

        # Verify response structure
        assert data["statementHandle"] == statement_handle
        assert "cancelled" in data
        assert data["cancelled"] is False  # Stub always returns False
        assert "status" in data

        # Verify status structure
        assert data["status"]["state"] == "NOT_IMPLEMENTED"

    def test_endpoints_accessible_via_openapi(self):
        """Test that endpoints are documented in OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()
        paths = openapi_schema["paths"]

        # Verify all three endpoints are in the schema
        assert "/api/v2/statements" in paths
        assert "/api/v2/statements/{statementHandle}" in paths
        assert "/api/v2/statements/{statementHandle}/cancel" in paths

    def test_statement_handle_with_special_characters(self):
        """Test endpoints handle statement handles with special characters."""
        special_handle = "handle-with-dashes_and_underscores.123"

        # Test get status
        response = client.get(f"/api/v2/statements/{special_handle}")
        assert response.status_code == 501
        assert response.json()["statementHandle"] == special_handle

        # Test cancel
        response = client.post(f"/api/v2/statements/{special_handle}/cancel")
        assert response.status_code == 501
        assert response.json()["statementHandle"] == special_handle
