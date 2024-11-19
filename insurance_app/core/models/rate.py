from datetime import date

from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from .base import Base


class Rate(Base):
    cargo_date: Mapped[date] = mapped_column(Date, primary_key=True)
    cargo_type: Mapped[str] = mapped_column(String, primary_key=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("cargo_date", "cargo_type", name="_date_cargo_type_pk"),
    )
