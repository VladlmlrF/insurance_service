from datetime import date as date_type

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from insurance_app.api.api_v1.rates.schemas import RateSchema
from insurance_app.core.models import Rate
from insurance_app.logger import logger


def get_rate(session: Session, date: date_type, cargo_type: str) -> Rate:
    """Get rate by date and cargo_type"""
    logger.info(f"Retrieving rate with date: {date} and cargo type: {cargo_type}")
    try:
        statement = (
            select(Rate)
            .where(and_(Rate.cargo_type == cargo_type, Rate.cargo_date <= date))
            .order_by(Rate.cargo_date.desc())
        )
        rate = session.execute(statement).scalars().first()
        if not rate:
            logger.info(f"Rate not found for date: {date} and cargo type: {cargo_type}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rate not found for cargo type '{cargo_type}' on or before date '{date}'",
            )
        logger.info(
            f"Rate retrieved: {rate.rate} for date: {rate.cargo_date} and cargo type: {cargo_type}"
        )
        return rate
    except SQLAlchemyError as error:
        logger.error(
            f"Failed to retrieve rate for date: {date} and cargo type: {cargo_type} "
            f"due to database error: {error}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rate due to database error",
        )


def create_rates(session: Session, rates: list[RateSchema]) -> None:
    """Create rates"""
    if not rates:
        logger.info("No rates to process")
        return
    logger.info("Creating rates")
    try:
        for rate in rates:
            db_rate = Rate(
                cargo_date=rate.cargo_date, cargo_type=rate.cargo_type, rate=rate.rate
            )
            session.merge(db_rate)
        session.commit()
        logger.info(f"{len(rates)} rates processed successfully")
    except SQLAlchemyError as error:
        session.rollback()
        logger.error(
            f"Failed to create rates due to database error: {error}", exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create rates due to database error",
        )
