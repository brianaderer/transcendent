"""A range of whole days, first and last included, as the Explore page asks for them."""

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta


class InvalidRange(Exception):
    pass


@dataclass(frozen=True)
class DayRange:
    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise InvalidRange(f"the range ends before it starts ({self.start} to {self.end})")

    @property
    def length(self) -> int:
        return (self.end - self.start).days + 1

    def days(self) -> Iterator[date]:
        return (self.start + timedelta(days=n) for n in range(self.length))

    def period_before(self) -> "DayRange":
        """The days of the same length just before this range."""
        return DayRange(self.start - timedelta(days=self.length), self.start - timedelta(days=1))

    def __contains__(self, day: date) -> bool:
        return self.start <= day <= self.end
