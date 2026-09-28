from unittest import mock

from alpaca_backtrader_api.fxmacrodata import FXMacroDataClient


def _fake_response(payload=b"{}"):
    resp = mock.MagicMock()
    resp.read.return_value = payload
    resp.__enter__.return_value = resp
    return resp


def test_request_forwards_zero_timeout():
    client = FXMacroDataClient(api_key="", base_url="https://example.test/v1")
    with mock.patch(
        "urllib.request.urlopen", return_value=_fake_response()
    ) as urlopen:
        client.request("calendar/usd", timeout=0)
    assert urlopen.call_args.kwargs["timeout"] == 0


def test_request_uses_client_timeout_when_not_overridden():
    client = FXMacroDataClient(
        api_key="", base_url="https://example.test/v1", timeout=7
    )
    with mock.patch(
        "urllib.request.urlopen", return_value=_fake_response()
    ) as urlopen:
        client.request("calendar/usd")
    assert urlopen.call_args.kwargs["timeout"] == 7


def test_request_sends_api_key_header_not_query():
    client = FXMacroDataClient(
        api_key="test-key", base_url="https://example.test/v1"
    )
    with mock.patch(
        "urllib.request.urlopen", return_value=_fake_response(b'{"a": 1}')
    ) as urlopen:
        result = client.request("/calendar/usd", {"limit": 5})
    req = urlopen.call_args.args[0]
    assert req.full_url == "https://example.test/v1/calendar/usd?limit=5"
    assert req.get_header("X-api-key") == "test-key"
    assert result == {"a": 1}


def test_request_omits_api_key_header_without_key(monkeypatch):
    monkeypatch.delenv("FXMACRODATA_API_KEY", raising=False)
    monkeypatch.delenv("FXMD_API_KEY", raising=False)
    client = FXMacroDataClient(base_url="https://example.test/v1")
    with mock.patch(
        "urllib.request.urlopen", return_value=_fake_response()
    ) as urlopen:
        client.request("calendar/usd")
    req = urlopen.call_args.args[0]
    assert not req.has_header("X-api-key")
