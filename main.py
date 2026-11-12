from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

@dataclass
class Quote:
    policy_id: str
    premium: Decimal
    start_date: datetime

q = Quote("P1", "lots", "tomorrow")
print(q)

print(q.premium * 2)