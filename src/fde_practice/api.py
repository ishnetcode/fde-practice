import asyncio
import time
from decimal import Decimal
from typing import Annotated

from fde_practice.errors import AppError
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fde_practice.quote_request import QuoteRequestDto
from fde_practice.quote_response import QuoteResponseDto
from fde_practice.quote_store import QuoteStore
from fde_practice.rate_client import RateClient

app = FastAPI()
quote_store = QuoteStore()


def get_rate_client() -> RateClient:
    return RateClient()


def get_quote_store() -> QuoteStore:
    return quote_store

StoreDep = Annotated[QuoteStore, Depends(get_quote_store)]
RatesDep = Annotated[RateClient, Depends(get_rate_client)]


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"errors": exc.errors()})


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    # Registered once, it catches AppError AND every subclass, so all four
    # rate errors, plus any you add later, come through here.

    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    # Use the status code and message the exception carries. The response shape
    # {"detail": ...} matches FastAPI's own HTTPException, so clients see one consis


@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.get("/slow-blocking/{n}")
async def slow_blocking(n: int):
    time.sleep(5)  # noqa: ASYNC251 - deliberate blocking call for the async demo
    # `noqa` = "no quality assurance" on this line. Naming the rule code
    # (rather than a bare `# noqa`) silences only this one warning, and the
    # comment tells future readers why.
    return {"n": n}


@app.get("/slow-async/{n}")
async def slow_async(n: int):
    await asyncio.sleep(5)  # non-blocking wait
    return {"n": n}


def to_response(quote_id: int, quote: QuoteRequestDto) -> QuoteResponseDto:
    if quote is None:
        raise ValueError("Quote cannot be None")
    return QuoteResponseDto(
        quote_id=quote_id,
        policy_id=quote.policy_id,
        premium=quote.premium,
        drivers=len(quote.drivers),
    )


@app.get("/quotes/{quote_id}", response_model=QuoteResponseDto)
def get_quote(quote_id: int, store: StoreDep):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return to_response(quote_id, quote)


@app.get("/quotes", response_model=list[QuoteResponseDto])
def get_stored_quotes(store:  StoreDep):
    return [to_response(quote_id, quote) for quote_id, quote in store.list_all()]

@app.post("/quotes", status_code=201, response_model=QuoteResponseDto)
def create_quote(
    request: QuoteRequestDto, 
    store: StoreDep
):
    quote_id = store.add(request)
    return to_response(quote_id, request)


@app.get("/quotes/{quote_id}/premium")
async def get_premium_in_currency(
    quote_id: int,
    store: StoreDep,
    rates: RatesDep,
    currency: str = "EUR",
):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")

    rate = await rates.get_rate("GBP", currency)
    converted = (quote.premium * rate).quantize(Decimal("0.01"))
    return {
        "quote_id": quote_id,
        "currency": currency,
        "rate": rate,
        "premium": converted,
    }


@app.get("/quotes/{quote_id}/premiums")
async def get_premiums_in_currencies(
    quote_id: int,
    store: StoreDep,
    rates: RatesDep,
    currencies: str = "EUR,USD",
):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    codes = [code.strip().upper() for code in currencies.split(",")]

    rate_list = await asyncio.gather(*(rates.get_rate("GBP", code) for code in codes))

    return {
        "quote_id": quote_id,
        "premiums": {
            code: (quote.premium * rate).quantize(Decimal("0.01"))
            for code, rate in zip(codes, rate_list)
        },
    }
