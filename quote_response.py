from decimal import Decimal
from pydantic import BaseModel

class QuoteResponseDto(BaseModel):
    quote_id: int
    policy_id: str
    premium: Decimal
    drivers: int