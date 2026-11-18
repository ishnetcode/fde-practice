from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, ValidationError, field_validator


class Quote(BaseModel):
    policy_id: str = Field(
        min_length=1, max_length=50, description="The unique identifier for the policy"
    )
    premium: Decimal = Field(gt=0, description="The premium amount for the policy")
    start_date: datetime

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, value):
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return value


try:
    q = Quote(policy_id="P1", premium="0", start_date="tomorrow")
except ValidationError as e:
    for error in e.errors():
        print(error["loc"][0], ":", error["msg"])
        # print(".".join(('drivers', 2, 'age')))
        print(str(2))
        loc = ("drivers", 2, "age")
        print([str(p) for p in loc])
        print(".".join([str(p) for p in loc]))
        field = ".".join([str(p) for p in error["loc"]])
        print(f"{field}: {error['msg']}")
else:
    print(q)
    print(type(q.premium), type(q.start_date))
    print(q.premium * 2)
