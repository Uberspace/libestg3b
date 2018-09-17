import datetime
from decimal import Decimal
from inspect import signature
from typing import List, Optional

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

    def __str__(self):
        return f'<Matcher: {self._description}>'


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
    matchers: List[Matcher]


M = Matcher

matchers = {
    'de': (
        (
            M(
                'Nachtarbeit 20:00-06:00', lambda m: m.hour >= 20 or m.hour < 6, multiply=Decimal('0.25'),
                tests=(
                    ('~19:59', False),
                    ('~20:00', True),
                    ('~21:00', True),
                    ('~05:59', True),
                    ('~06:00', False),
                ),
            ),
            M(
                'Nachtarbeit 00:00-04:00 (Folgetag)', lambda m, f: 0 <= m.hour < 4 and f.date() < m.date(), multiply=Decimal('0.4'),
                tests=(
                    ('00:00~00:01', False),
                    ('23:59~00:01', True),
                    ('23:59~03:59', True),
                    ('23:59~04:00', False),
                )
            ),
        ),
        (
            M(
                'Sonntagsarbeit', lambda m: m.weekday() == 6, multiply=Decimal('0.5'),
                tests=(
                    ('~2018-09-15', False),
                    ('~2018-09-16 00:00', True),
                    ('~2018-09-16 23:59', True),
                    ('2018-09-16 23:59~2018-09-17 00:00', False),
                ),
            ),
            M(
                'Sonntagsarbeit (Montag)', lambda m, f: f.weekday() == 6 and 0 <= m.hour < 4, multiply=Decimal('0.5'),
                tests=(
                    # 2018-09-16 is a Sunday
                    ('~2018-09-16 00:00', False),
                    ('~2018-09-16 23:59', False),
                    ('2018-09-16 23:59~2018-09-17 00:00', True),
                    ('2018-09-16 23:59~2018-09-17 03:59', True),
                    ('2018-09-16 23:59~2018-09-17 04:00', False),
                    ('2018-09-17 23:59~2018-09-18 00:00', False),
                ),
            ),
            M(
                'Feiertagsarbeit', lambda m, f, holidays: m in holidays, multiply=Decimal('1.25'),
                tests=(
                    # 2018-05-10 is Christi Himmelfahrt
                    ('~2018-05-09 23:59', False),
                    ('~2018-05-10 00:00', True),
                    ('~2018-05-10 23:59', True),
                    ('~2018-05-11 00:00', False),
                    ('2018-05-10 23:59~2018-05-11 00:00', False),
                ),
            ),
            M(
                'Feiertagsarbeit (Folgetag)', lambda m, f, holidays: f in holidays and 0 <= m.hour < 4, multiply=Decimal('1.25'),
                tests=(
                    # 2018-05-10 is Christi Himmelfahrt
                    ('~2018-05-10 00:00', False),
                    ('~2018-05-10 23:59', False),
                    ('2018-05-10 23:59~2018-05-11 00:00', True),
                    ('2018-05-10 23:59~2018-05-11 03:59', True),
                    ('2018-05-10 23:59~2018-05-11 04:00', False),
                    ('2018-09-11 23:59~2018-05-12 00:00', False),
                )
            ),
            DayTimeMatcher(12, 24, 14, multiply=Decimal('1.25')),
            DayTimeMatcher(12, 31, 14, multiply=Decimal('1.25')),
            DayMatcher(12, 25, multiply=Decimal('1.5')),
            DayMatcher(12, 26, multiply=Decimal('1.5')),
            DayMatcher(5, 1, multiply=Decimal('1.5')),
        ),
    ),
}
