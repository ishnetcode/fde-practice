from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from quote_request import QuoteRequestDto
from quote_response import QuoteResponseDto

app = FastAPI()

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=400, content={"errors": exc.errors()})

@app.get("/")
def read_root():
    return {"message": "Hello World"}

quotes: dict[int, QuoteRequestDto] = {}
next_quote_id: int = 1

@app.get("/quotes/{quote_id}", response_model=QuoteResponseDto)
def get_quote(quote_id: int):
    if quote_id not in quotes:
        raise HTTPException(status_code=404, detail="Quote not found")
    return to_response(quote_id, quotes[quote_id])

@app.get("/quotes", response_model=list[QuoteResponseDto])
def get_stored_quotes():
    quotes_list = []
    for quote_id,  quote in quotes.items():
        quotes_list.append(to_response(quote_id, quote))
    return quotes_list
# return [to_response(quote_id, quote) for quote_id, quote in quotes.items()]

@app.post("/quotes", status_code=201, response_model=QuoteResponseDto)
def create_quote(request: QuoteRequestDto):
    global next_quote_id
    quote_id = next_quote_id
    quotes[quote_id] = request
    next_quote_id += 1
    return to_response(quote_id, request)

  
def to_response(quote_id: int, quote: QuoteRequestDto | None) -> QuoteResponseDto:
    if quote is None:
        raise ValueError("Quote cannot be None")
    return QuoteResponseDto(
        quote_id=quote_id,
        policy_id=quote.policy_id,
        premium=quote.premium,
        drivers=len(quote.drivers)
    )
    
if __name__ == "__main__":
    to_response(1, None)  # This is just to check the function signature and type hints. It will raise an error if the types are incorrect.