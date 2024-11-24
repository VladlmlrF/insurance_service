from datetime import date

from pydantic import BaseModel


class RateBaseSchema(BaseModel):
    cargo_date: date
    cargo_type: str


class RateUpdateSchema(BaseModel):
    cargo_date: date | None = None
    cargo_type: str | None = None
    rate: float | None = None


class RateSchema(RateBaseSchema):
    rate: float


class InsuranceRequest(BaseModel):
    cargo_date: date
    cargo_type: str
    declared_value: float
