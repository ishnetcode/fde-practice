from datetime import datetime
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field, ValidationError, field_validator


class CoverType(str, Enum):
    COMPREHENSIVE = "comprehensive"
    THIRD_PARTY_FIRE_THEFT = "third-party-fire-theft"
    THIRD_PARTY = "third-party"


class DriverDto(BaseModel):
    full_name: str = Field(
        min_length=1, max_length=100, description="The name of the driver"
    )
    age: int = Field(le=99, ge=17, description="The age of the driver")
    years_no_claims: int | None = Field(
        default=None, ge=0, description="The number of years without claims"
    )


class QuoteRequestDto(BaseModel):
    policy_id: str = Field(
        min_length=2, max_length=20, description="The unique identifier for the policy"
    )
    cover_type: CoverType
    # premium: Decimal = Field(ge=0.01, description="The premium amount for the policy")
    # ge=0.01 passes a float into a money check. gt=0 (as before) or ge=Decimal("0.01") avoids mixing floats with Decimal.
    premium: Decimal = Field(gt=0, description="The premium amount for the policy")
    start_date: datetime = Field(description="The start date for the policy")
    drivers: list[DriverDto] = Field(
        min_length=1, description="A list of drivers associated with the policy"
    )

    @field_validator("start_date", mode="before")
    @classmethod
    def validate_start_date(cls, value):
        try:
            return datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            return value


if __name__ == "__main__":
    try:
        q = QuoteRequestDto(
            policy_id="P1",
            cover_type="comprehensive",
            premium=Decimal("0.01"),
            start_date="15/09/2026",
            drivers=[
                {"full_name": "John Doe", "age": 17, "years_no_claims": 2},
                {"full_name": "Jane Smith", "age": 16, "years_no_claims": 5},
                {"full_name": "Sean Smith", "age": 27},
            ],
        )
    except ValidationError as e:
        for error in e.errors():
            field = ".".join([str(p) for p in error["loc"]])
            print(f"{field}: {error['msg']}")
    else:
        print(q)
        print("-" * 40)
        print(q.drivers[0].full_name, q.drivers[0].age, q.drivers[0].years_no_claims)
