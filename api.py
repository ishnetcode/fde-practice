from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from quote_request import QuoteRequestDto
from quote_response import QuoteResponseDto
from quote_store import QuoteStore
import time
import asyncio

app = FastAPI()
quote_store = QuoteStore()

def get_quote_store() -> QuoteStore:
    return quote_store

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"errors": exc.errors()})

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/slow-blocking/{n}")
async def slow_blocking(n: int):
    time.sleep(5)              # blocking call inside async def
    return {"n": n}

@app.get("/slow-async/{n}")
async def slow_async(n: int):
    await asyncio.sleep(5)     # non-blocking wait
    return {"n": n}

def to_response(quote_id: int, quote: QuoteRequestDto) -> QuoteResponseDto:
    if quote is None:
        raise ValueError("Quote cannot be None")
    return QuoteResponseDto(
        quote_id=quote_id,
        policy_id=quote.policy_id,
        premium=quote.premium,
        drivers=len(quote.drivers)
    )

@app.get("/quotes/{quote_id}", response_model=QuoteResponseDto)
def get_quote(quote_id: int, store: QuoteStore = Depends(get_quote_store)):
    quote = store.get(quote_id)
    if quote is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return to_response(quote_id, quote)

@app.get("/quotes", response_model=list[QuoteResponseDto])
def get_stored_quotes(store: QuoteStore = Depends(get_quote_store)):
    return [to_response(quote_id, quote) for quote_id, quote in store.list_all()]

@app.post("/quotes", status_code=201, response_model=QuoteResponseDto)
def create_quote(request: QuoteRequestDto, store: QuoteStore = Depends(get_quote_store)):
    quote_id = store.add(request)
    return to_response(quote_id, request)

  

