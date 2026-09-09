import json
from StockSageAI import api_gateway


def test_health_endpoint_returns_payload(monkeypatch):
    """Small unit test for the top-level /health endpoint.

    This monkeypatches `build_health_payload` to return a deterministic
    payload so the test does not depend on DB or external services.
    """
    expected = {
        'status': 'operational',
        'timestamp': '2026-09-09T00:00:00',
        'version': '1.0.0',
        'checks': {}
    }

    # Replace the real health builder with a deterministic stub
    monkeypatch.setattr(api_gateway, 'build_health_payload', lambda: expected)

    client = api_gateway.app.test_client()
    resp = client.get('/health')

    assert resp.status_code == 200
    data = resp.get_json()
    assert data == expected
