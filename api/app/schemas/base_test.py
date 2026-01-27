"""Tests for base schema utilities."""

from app.schemas.base import error_response, success_response


def test_success_response_format():
    """Test success_response creates proper envelope."""
    result = success_response({"key": "value"})

    assert result["success"] is True
    assert result["data"] == {"key": "value"}
    assert result["error"] is None


def test_success_response_with_none_data():
    """Test success_response handles None data."""
    result = success_response(None)

    assert result["success"] is True
    assert result["data"] is None
    assert result["error"] is None


def test_error_response_format():
    """Test error_response creates RFC 7807 format."""
    result = error_response(
        type_uri="https://athena.example/errors/not-found",
        title="Not Found",
        status=404,
        detail="Resource not found",
        instance="/api/test",
    )

    assert result["success"] is False
    assert result["data"] is None
    assert result["error"]["type"] == "https://athena.example/errors/not-found"
    assert result["error"]["title"] == "Not Found"
    assert result["error"]["status"] == 404
    assert result["error"]["detail"] == "Resource not found"
    assert result["error"]["instance"] == "/api/test"
