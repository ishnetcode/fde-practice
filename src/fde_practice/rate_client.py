from decimal import Decimal  # Decimal for money and rates, never float (Day 2 lesson).

import httpx  # The async-capable HTTP client: Python's HttpClient. It came with fastapi[standard].
from fde_practice.errors import (
    AppError,
    RateServiceBadResponseError,
    RateServiceTimeoutError,
    RateServiceUnavailableError,
    UnsupportedCurrencyError,
)  # Brackets let one import span several lines. Same import, just more readable.


def translate_http_error(error: httpx.HTTPError, currency: str) -> AppError:
    # Takes any httpx failure and RETURNS the matching domain exception (it doesn't
    # raise it). Written once and reused by every method that calls the rate API.

    match error:
        # Python's `match` statement (3.10+), like a C# switch with type patterns:
        #   switch (error) { case TimeoutException: ... }
        # Cases are checked top to bottom; the first match wins.

        case httpx.TimeoutException():
            return RateServiceTimeoutError()
            # `httpx.TimeoutException()` in a case is a TYPE CHECK, not a
            # constructor call: "is error a TimeoutException?"
            # Like `case TimeoutException:` in C#.

        case httpx.HTTPStatusError() if 400 <= error.response.status_code < 500:
            return UnsupportedCurrencyError(currency)
            # Type check plus an extra condition (a "guard"), like C#'s
            # `case HttpStatusError e when e.StatusCode < 500:`

        case httpx.HTTPStatusError():
            return RateServiceBadResponseError()
            # Any other status error (5xx) lands here.

        case _:
            return RateServiceUnavailableError()
            # `_` matches anything: the `default:` branch. Network failures end up here.


class RateClient:
    BASE_URL = "https://api.frankfurter.dev/v1/latest"

    async def get_rate(self, from_currency: str, to_currency: str) -> Decimal:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={"base": from_currency, "symbols": to_currency},
                )
                response.raise_for_status()

        except httpx.HTTPError as e:
            raise translate_http_error(e, to_currency) from e
            # One catch for every httpx failure. The translator picks the right
            # domain exception, we raise it, and `from e` keeps the original as the cause.)
            
        rate = response.json()["rates"].get(to_currency)
        # Read the rate from the JSON. .get returns None instead of raising KeyError
        # if the service left this currency out.

        if rate is None:
            raise UnsupportedCurrencyError(to_currency)
            # The service answered 200 but without our currency. That's the client's
            # bad input, so it becomes a 400 through the global handler.

        return Decimal(str(rate))
