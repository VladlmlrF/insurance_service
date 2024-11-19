from datetime import date

from pydantic import BaseModel


class RateSchema(BaseModel):
    cargo_date: date
    cargo_type: str
    rate: float


class InsuranceRequest(BaseModel):
    cargo_date: date
    cargo_type: str
    declared_value: float
