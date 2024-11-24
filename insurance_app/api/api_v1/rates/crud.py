from datetime import date as date_type
from datetime import datetime
from datetime import timezone

from fastapi import HTTPException
from fastapi import status
from sqlalchemy import and_
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from insurance_app.api.api_v1.rates.schemas import RateSchema
from insurance_app.api.api_v1.rates.schemas import RateUpdateSchema
from insurance_app.core.models import Rate
from insurance_app.kafka_producer import KafkaProducer
from insurance_app.logger import logger

KAFKA_SERVERS = ["kafka:9092"]
kafka_producer = KafkaProducer(servers=KAFKA_SERVERS)


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


def create_rates(
    session: Session,
    rates: list[RateSchema],
    user_id: int | None = None,
) -> None:
    """Create rates"""
    if not rates:
        logger.info("No rates to process")
        return
    logger.info("Creating rates")
    message = {
        "user_id": user_id,
        "action": "create_rates",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": {
            "rates_count": len(rates),
            "rates": [rate.model_dump() for rate in rates],
        },
    }
    kafka_producer.send("rate_changes", message)
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


def update_rate(
    session: Session,
    cargo_date: date_type,
    cargo_type: str,
    rate_update: RateUpdateSchema,
    user_id: int | None = None,
) -> Rate:
    """Update rate by cargo_date and cargo_type"""
    logger.info(f"Updating rate for date: {cargo_date} and cargo type: {cargo_type}")
    try:
        rate = get_rate(session, cargo_date, cargo_type)
        for name, value in rate_update.model_dump(exclude_unset=True).items():
            setattr(rate, name, value)
        session.commit()
        session.refresh(rate)
        logger.info(
            f"Rate updated successfully for date: {cargo_date} and cargo type: {cargo_type}"
        )
        message = {
            "user_id": user_id,
            "action": "update_rate",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {
                "cargo_date": str(cargo_date),
                "cargo_type": cargo_type,
                "updated_fields": rate_update.model_dump(exclude_unset=True),
            },
        }
        kafka_producer.send("rate_changes", message)
        return rate
    except SQLAlchemyError as error:
        session.rollback()
        logger.error(
            f"Failed to update rate for date: {cargo_date} and cargo type: {cargo_type} "
            f"due to database error: {error}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update rate due to database error",
        )


def delete_rate(
    session: Session,
    cargo_date: date_type,
    cargo_type: str,
    user_id: int | None = None,
) -> None:
    """Delete rate by cargo_date and cargo_type"""
    logger.info(f"Deleting rate for date: {cargo_date} and cargo type: {cargo_type}")
    try:
        rate = get_rate(session, cargo_date, cargo_type)
        session.delete(rate)
        session.commit()
        logger.info(
            f"Rate deleted successfully for date: {cargo_date} and cargo type: {cargo_type}"
        )
        message = {
            "user_id": user_id,
            "action": "delete_rate",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": {"cargo_date": str(cargo_date), "cargo_type": cargo_type},
        }
        kafka_producer.send("rate_changes", message)
    except SQLAlchemyError as error:
        session.rollback()
        logger.error(
            f"Failed to delete rate for date: {cargo_date} and cargo type: {cargo_type} "
            f"due to database error: {error}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete rate due to database error",
        )
