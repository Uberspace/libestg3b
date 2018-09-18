import datetime
import inspect
import itertools
from decimal import Decimal

import holidays
from dateutil.relativedelta import relativedelta

from .matcher import DayMatcher, DayTimeMatcher, Match
from .matcher import Matcher as M
from .matcher import MatcherGroup


def EstG3b(country):
    try:
        country_estg3b = globals()['EstG3b' + country]()
    except (KeyError):
        raise KeyError("Country %s not available" % country)
    return country_estg3b


def EstG3bs():
    return [clazz for clazz in globals().values() if inspect.isclass(clazz) and issubclass(clazz, EstG3bBase) and clazz != EstG3bBase]


class EstG3bBase:
    def __init__(self, country, groups, add_matchers=None, replace_matchers=None) -> None:
        self._holidays = holidays.CountryHoliday(country.upper())
        self._groups = groups

        if replace_matchers:
            self._groups = replace_matchers.copy()
        if add_matchers:
            self._groups.extend(add_matchers)

        assert self._groups
        assert all(lambda g: isinstance(g, MatcherGroup) for g in self._groups)

    def _list_minutes(self, start, end):
        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)

        while start < end:
            yield start
            start = start + relativedelta(minutes=1)

    def calculate_shift(self, shift):
        assert len(shift) == 2
        assert isinstance(shift[0], datetime.datetime)
        assert isinstance(shift[1], datetime.datetime)

        minutes = self._list_minutes(shift[0], shift[1])
        start = next(minutes)
        minutes = itertools.chain([start], minutes)

        matches = []

        for minute in minutes:
            minute_matchers = set(
                group.match(minute, start, self._holidays)
                for group in self._groups
            )
            minute_matchers.discard(None)

            if matches and matches[-1].matchers == minute_matchers:
                # combine equal matches by increasing the length of the last one
                matches[-1].end = matches[-1].end + relativedelta(minutes=1)
            else:
                # a list of minutes is inclusive the last one, the `end` stamp is exclusive
                matches.append(Match(minute, minute + relativedelta(minutes=1), minute_matchers))

        return matches

    def calculate_shifts(self, shifts):
        return map(self.calculate_shift, shifts)


class EstG3bGermany(EstG3bBase):
    def __init__(self, **kwargs):
        matchers = (
            MatcherGroup('Nachtarbeit', (
                M(
                    'DE_NIGHT', 'Nachtarbeit 20:00-06:00',
                    lambda m: m.hour >= 20 or m.hour < 6, multiply=Decimal('0.25'),
                    tests=(
                        ('~19:59', False),
                        ('~20:00', True),
                        ('~21:00', True),
                        ('~05:59', True),
                        ('~06:00', False),
                    ),
                ),
                M(
                    'DE_NIGHT_00_04', 'Nachtarbeit 00:00-04:00 (Folgetag)',
                    lambda m, s: 0 <= m.hour < 4 and s.date() < m.date(), multiply=Decimal('0.4'),
                    tests=(
                        ('00:00~00:01', False),
                        ('23:59~00:01', True),
                        ('23:59~03:59', True),
                        ('23:59~04:00', False),
                    )
                ),
            )),
            MatcherGroup('Sonntags und Feiertagsarbeit', (
                M(
                    'DE_SUNDAY', 'Sonntagsarbeit',
                    lambda m: m.weekday() == 6, multiply=Decimal('0.5'),
                    tests=(
                        ('~2018-09-15', False),
                        ('~2018-09-16 00:00', True),
                        ('~2018-09-16 23:59', True),
                        ('2018-09-16 23:59~2018-09-17 00:00', False),
                    ),
                ),
                M(
                    'DE_SUNDAY_NEXT_NIGHT', 'Sonntagsarbeit (Montag)',
                    lambda m, s: s.weekday() == 6 and 0 <= m.hour < 4, multiply=Decimal('0.5'),
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
                    'DE_HOLIDAY', 'Feiertagsarbeit',
                    lambda m, s, holidays: m in holidays, multiply=Decimal('1.25'),
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
                    'DE_HOLIDAY_NEXT_NIGHT', 'Feiertagsarbeit (Folgetag)',
                    lambda m, s, holidays: s in holidays and 0 <= m.hour < 4, multiply=Decimal('1.25'),
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
                DayTimeMatcher('DE_CHRISTMAS_EVE', 12, 24, 14, multiply=Decimal('1.25')),
                DayTimeMatcher('DE_NEWYEARS_EVE', 12, 31, 14, multiply=Decimal('1.25')),
                DayMatcher('DE_CHRISTMAS', 12, 25, multiply=Decimal('1.5')),
                DayMatcher('DE_STEFANITAG', 12, 26, multiply=Decimal('1.5')),
                DayMatcher('DE_NEWYEARS', 5, 1, multiply=Decimal('1.5')),
            )),
        )
        super().__init__('DE', matchers, **kwargs)


EstG3bDE = EstG3bGermany
