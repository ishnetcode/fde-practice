import asyncio
from decimal import Decimal
from typing import ClassVar

import pytest
from api import app, get_quote_store, get_rate_client
from errors import RateServiceUnavailableError, UnsupportedCurrencyError
from fastapi.testclient import TestClient
from quote_store import QuoteStore

VALID_PAYLOAD = {
    "policy_id": "P1",
    "cover_type": "comprehensive",
    "premium": "250.00",
    "start_date": "15/09/2026",
    "drivers": [{"full_name": "John Doe", "age": 30}],
}


class FakeRateClient:
    def __init__(self, rate: Decimal):
        self.rate = rate
        self.calls: list[tuple[str, str]] = []

    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        self.calls.append((from_currency, to_currency))
        return self.rate


class FakeRateClientWithError:
    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        raise RateServiceUnavailableError()


class FakeRateClientWithUnsupportedCurrency:
    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        raise UnsupportedCurrencyError(to_currency)


@pytest.fixture
def client():
    fresh_store = QuoteStore()  # Create a fresh instance of QuoteStore for each test
    app.dependency_overrides[get_quote_store] = lambda: fresh_store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_another_quote_creation(client):
    # Arrange
    request_data = {
        "policy_id": "P2",
        "cover_type": "third-party",
        "premium": "150.00",
        "start_date": "01/01/2025",
        "drivers": [{"full_name": "Jane Smith", "age": 28}],
    }

    # Act
    create_response = client.post("/quotes", json=request_data)

    # Retrieve the quote
    assert create_response.status_code == 201


def test_create_quote_returns_201_and_quote_id(client):
    # Arrange
    request_data = {
        "policy_id": "P1",
        "cover_type": "comprehensive",
        "premium": "250.00",
        "start_date": "15/09/2026",
        "drivers": [{"full_name": "John Doe", "age": 30}],
    }

    # Act
    response = client.post("/quotes", json=request_data)

    # Assert
    assert response.status_code == 201
    response_data = response.json()
    assert response_data["quote_id"] == 1
    assert response_data["policy_id"] == request_data["policy_id"]
    assert Decimal(response_data["premium"]) == Decimal(request_data["premium"])
    assert response_data["drivers"] == len(request_data["drivers"])


def test_get_missing_quote_returns_404(client):
    # Act
    response = client.get("/quotes/999")  # Assuming quote_id 999 does not exist

    # Assert
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["detail"] == "Quote not found"


def test_premium_is_converted_using_rate(client):
    fake = FakeRateClient(Decimal("1.20"))
    app.dependency_overrides[get_rate_client] = lambda: fake
    quote_id = client.post("/quotes", json=VALID_PAYLOAD).json()["quote_id"]

    response = client.get(f"/quotes/{quote_id}/premium", params={"currency": "EUR"})

    assert response.status_code == 200
    assert Decimal(response.json()["premium"]) == Decimal("300.00")
    assert fake.calls == [("GBP", "EUR")]


def test_premium_conversion_for_missing_quote_returns_503(client):
    fake = FakeRateClientWithError()
    app.dependency_overrides[get_rate_client] = lambda: fake
    quote_id = client.post("/quotes", json=VALID_PAYLOAD).json()["quote_id"]

    response = client.get(f"/quotes/{quote_id}/premium", params={"currency": "EUR"})

    assert response.status_code == 503


class FakeRateClientWithDelays:
    # A fake where each currency takes a different amount of time, so the calls
    # deliberately finish in a different order from how they started.

    RATES: ClassVar[dict[str, Decimal]] = {"EUR": Decimal("1.10"), "USD": Decimal("1.30")}
    DELAYS: ClassVar[dict[str, float]] = {"EUR": 0.2, "USD": 0.0}
    # ClassVar: "deliberately shared by the whole class", the equivalent of
    # `static readonly` in intent. ruff accepts it as intentional.

    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        await asyncio.sleep(self.DELAYS[to_currency])
        # Non-blocking wait: EUR waits 0.2s, USD returns at once.
        return self.RATES[to_currency]


def test_multi_currency_rates_stay_matched_to_their_currency(client):
    app.dependency_overrides[get_rate_client] = lambda: FakeRateClientWithDelays()
    quote_id = client.post("/quotes", json=VALID_PAYLOAD).json()["quote_id"]
    # Arrange: a 250.00 premium, and a fake where USD finishes before EUR.

    response = client.get(
        f"/quotes/{quote_id}/premiums", params={"currencies": "EUR,USD"}
    )
    # Act: EUR is requested first, but it finishes second.

    premiums = response.json()["premiums"]
    assert Decimal(premiums["EUR"]) == Decimal("275.00")  # 250.00 * 1.10
    assert Decimal(premiums["USD"]) == Decimal("325.00")  # 250.00 * 1.30
    # If results came back in completion order, these two values would be
    # swapped and the test would fail.


def test_multi_currency_rates_with_unsupported_currency(client):
    app.dependency_overrides[get_rate_client] = lambda: (
        FakeRateClientWithUnsupportedCurrency()
    )
    quote_id = client.post("/quotes", json=VALID_PAYLOAD).json()["quote_id"]
    response = client.get(f"/quotes/{quote_id}/premiums", params={"currencies": "XYZ"})
    assert response.status_code == 400
    assert "XYZ" in response.json()["detail"]
