import json
import os
import urllib.error
import urllib.parse
import urllib.request


def _clean_api_key(api_key):
    api_key = (api_key or "").strip()
    if any(char.isspace() for char in api_key) or not api_key.isprintable():
        # Never include the key itself in the message.
        raise ValueError("FXMacroData API key contains invalid characters")
    return api_key


class FXMacroDataClient:
    """Client for adding macro, calendar, COT, and FX context to strategies."""

    DEFAULT_BASE_URL = "https://api.fxmacrodata.com/v1/"

    def __init__(self, api_key=None, base_url=None, timeout=30):
        self.api_key = _clean_api_key(
            api_key
            or os.getenv("FXMACRODATA_API_KEY")
            or os.getenv("FXMD_API_KEY")
            or ""
        )
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/") + "/"
        self.timeout = timeout

    def request(self, path, params=None, timeout=None):
        """GET one page. History endpoints (announcements, predictions,
        forex, cot, commodities) return 20 rows by default; pass ``limit``
        (max 100) and ``offset`` and follow ``pagination.next_offset`` while
        ``pagination.has_more`` is true."""
        query = dict(params or {})
        url = urllib.parse.urljoin(self.base_url, path.lstrip("/"))
        if query:
            url = url + "?" + urllib.parse.urlencode(query)

        req = urllib.request.Request(
            url, headers={"Accept": "application/json"}
        )
        if self.api_key:
            # Unredirected headers are not copied onto a followed redirect,
            # so the key is never forwarded to another host.
            req.add_unredirected_header("X-API-Key", self.api_key)
        try:
            with urllib.request.urlopen(
                req, timeout=self.timeout if timeout is None else timeout
            ) as resp:
                payload = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                "FXMacroData request failed with HTTP {}: {}".format(
                    exc.code, body
                )
            )
        try:
            data = json.loads(payload)
        except ValueError:
            raise RuntimeError(
                "FXMacroData returned a non-JSON response for {}".format(path)
            ) from None
        if isinstance(data, dict) and "detail" in data and "data" not in data:
            raise RuntimeError(
                "FXMacroData request failed: {}".format(data["detail"])
            )
        return data

    def data_catalogue(self, currency):
        return self.request("data_catalogue/" + currency.lower())

    def announcements(self, currency, indicator, **params):
        path = "announcements/{}/{}".format(currency.lower(), indicator)
        return self.request(path, params)

    def latest_announcements(self, currency, **params):
        path = "announcements/{}/latest".format(currency.lower())
        return self.request(path, params)

    def calendar(self, currency, **params):
        return self.request("calendar/" + currency.lower(), params)

    def predictions(self, currency, indicator, **params):
        path = "predictions/{}/{}".format(currency.lower(), indicator)
        return self.request(path, params)

    def forex(self, base, quote="usd", **params):
        path = "forex/{}/{}".format(base.lower(), quote.lower())
        return self.request(path, params)

    def cot(self, currency, **params):
        return self.request("cot/" + currency.lower(), params)

    def commodity(self, indicator, **params):
        return self.request("commodities/" + indicator, params)

    def commodities_latest(self, **params):
        return self.request("commodities/latest", params)

    def rate_differentials(self, base, quote="usd", **params):
        path = "rate_differentials/{}/{}".format(base.lower(), quote.lower())
        return self.request(path, params)

    def market_sessions(self, **params):
        return self.request("market_sessions", params)

    def risk_sentiment(self, **params):
        return self.request("risk_sentiment", params)

    def macro_context(
        self, base, quote="usd", indicator="policy_rate", limit=10
    ):
        return {
            "base_catalogue": self.data_catalogue(base),
            "quote_catalogue": self.data_catalogue(quote),
            "base_calendar": self.calendar(base, limit=limit),
            "quote_calendar": self.calendar(quote, limit=limit),
            "base_announcements": self.announcements(
                base, indicator, limit=limit
            ),
            "quote_announcements": self.announcements(
                quote, indicator, limit=limit
            ),
            "forex": self.forex(base, quote, limit=limit),
        }
