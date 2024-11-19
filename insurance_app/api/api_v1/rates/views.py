import json
from pathlib import Path

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from sqlalchemy.orm import Session

from insurance_app.api.api_v1.rates import crud
from insurance_app.api.api_v1.rates.schemas import InsuranceRequest
from insurance_app.api.api_v1.rates.schemas import RateSchema
from insurance_app.core.models import db_helper

router = APIRouter(tags=["Rates"])


@router.post(
    "/load_rates",
    summary="Load Rates",
    description="Loads insurance rates from a JSON file into the database.",
)
def load_rates(session: Session = Depends(db_helper.get_db)):
    """
    Load insurance rates from a JSON file and store them in the database.

    This endpoint reads rates from the 'rates.json' file located in the data directory
    and saves them into the database.

    **Returns:**

    - A JSON object indicating the success status.
    """
    rates_file = (
        Path(__file__).parent.parent.parent.parent.parent / "data" / "rates.json"
    )
    with open(rates_file, "r") as file:
        rates_data = json.load(file)
    rates_list = []
    for date_str, rates in rates_data.items():
        for rate_info in rates:
            rate = RateSchema(
                cargo_date=date_str,
                cargo_type=rate_info["cargo_type"],
                rate=float(rate_info["rate"]),
            )
            rates_list.append(rate)
    crud.create_rates(session, rates_list)
    return {"status": "Rates loaded successfully"}


@router.post(
    "/calculate",
    summary="Calculate Insurance Cost",
    description="Calculates the insurance cost based on cargo type, date, and declared value.",
)
def calculate_insurance(
    request: InsuranceRequest, session: Session = Depends(db_helper.get_db)
):
    """
    Calculate the insurance cost for a given cargo type, date, and declared value.

    **Parameters:**

    - **request**: An object containing:
        - **cargo_date** (*date*): Date of the cargo.
        - **cargo_type** (*str*): Type of the cargo.
        - **declared_value** (*float*): Declared value of the cargo.

    **Returns:**

    - A JSON object containing the calculated insurance cost.

    **Raises:**

    - **HTTPException**: If the rate for the given cargo type and date is not found.
    """
    rate_record = crud.get_rate(session, request.cargo_date, request.cargo_type)
    if not rate_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Rate not found"
        )
    insurance_cost = request.declared_value * rate_record.rate
    return {"insurance_cost": insurance_cost}
