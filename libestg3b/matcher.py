import datetime
from decimal import Decimal
from inspect import signature
from typing import Optional, Set

import dateutil
from holidays import CountryHoliday

from dataclasses import dataclass


class Matcher():
    def __init__(self, description: str, impl, *, multiply: Optional[Decimal] = None, add: Optional[Decimal] = None, tests=[]) -> None:
        self._description = description
        self._impl = impl
        self._multiply = multiply
        self._add = add
        self._tests = tests

        assert (multiply is None) != (add is None)
        assert len(description) > 0
        assert 1 <= len(self._impl_parameters) <= 3

    @property
    def _impl_parameters(self):
        return signature(self._impl).parameters

    @property
    def _bonus(self):
        return self._multiply if self._multiply else self._add

    def _parse_test_time(self, tt):
        default = datetime.datetime(2018, 1, 10)
        return dateutil.parser.parse(tt, default=default) if tt else default

    def examples(self):
        for t in self._tests:
            first_minute, minute = t[0].split('~')
            minute = self._parse_test_time(minute)
            first_minute = self._parse_test_time(first_minute)

            if minute.time() < first_minute.time():
                minute = minute + dateutil.relativedelta.relativedelta(days=1)

            yield [
                minute,
                first_minute,
                t[1],
            ]

    def __call__(self, minute: datetime.datetime, first_minute: datetime.datetime, holidays: CountryHoliday) -> bool:
        narg = len(self._impl_parameters)

        if narg == 1:
            r = self._impl(minute)
        elif narg == 2:
            r = self._impl(minute, first_minute)
        elif narg == 3:
            r = self._impl(minute, first_minute, holidays)

        assert isinstance(r, bool)

        return r

    def __repr__(self):
        return f'<Matcher: {self._description}>'

    def __hash__(self):
        return hash(self._description)

    def __eq__(self, other):
        return self._description == other._description

    def __gt__(self, other):
        return self._bonus > other._bonus

    def __lt__(self, other):
        return self._bonus < other._bonus


class DayMatcher(Matcher):
    """ match, if the given minute is within the given day. Keyword arguments are passed onto Matcher. """
    def __init__(self, month: int, day: int, **kwargs) -> None:
        super().__init__(
            f'{month:02d}-{day:02d}',
            lambda m: m.month == month and m.day == day,
            **kwargs,
        )


class DayTimeMatcher(Matcher):
    """ match, if the given minute is within the given day after the given hour. Keyword arguments are passed onto Matcher. """
    def __init__(self, month: int, day: int, hour: int, **kwargs) -> None:
        super().__init__(
            f'{month:02d}-{day:02d} {hour:02d}:00+',
            lambda m: m.month == month and m.day == day and m.hour >= hour,
            **kwargs,
        )


@dataclass
class Match():
    start: datetime.datetime
    end: datetime.datetime
    matchers: Set[Matcher]
