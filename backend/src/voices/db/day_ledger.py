"""Queries on the day ledger (`ingested_days`, atlas plate 40) shared by the stores."""

from sqlalchemy import Select, func, select

from voices.db.models import IngestedDay


def latest_day_with_status(status: str) -> Select:
    return select(func.max(IngestedDay.day)).where(IngestedDay.status == status)
