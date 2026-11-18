from fde_practice.quote_request import QuoteRequestDto


class QuoteStore:
    def __init__(self):
        # the constructor: set up self._quotes and self._next_id here
        self._quotes: dict[int, QuoteRequestDto] = {}
        self._next_id: int = 1

    def add(self, quote: QuoteRequestDto) -> int:
        # store it, return the new id
        quote_id = self._next_id
        self._quotes[quote_id] = quote
        self._next_id += 1
        return quote_id

    def get(self, quote_id: int) -> QuoteRequestDto | None:
        # return the quote, or None if missing
        return self._quotes.get(quote_id)

    def list_all(self) -> list[tuple[int, QuoteRequestDto]]:
        # return (id, quote) pairs
        return list(self._quotes.items())
