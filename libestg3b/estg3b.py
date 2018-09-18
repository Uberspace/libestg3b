import datetime
import inspect
import itertools
from decimal import Decimal

import holidays
from dateutil.relativedelta import relativedelta

from .matcher import DayMatcher, DayTimeMatcher, Match
from .matcher import Matcher as M


def EstG3b(country):
    try:
        country_estg3b = globals()['EstG3b' + country]()
    except (KeyError):
        raise KeyError("Country %s not available" % country)
    return country_estg3b


def EstG3bs():
    return [clazz for clazz in globals().values() if inspect.isclass(clazz) and issubclass(clazz, EstG3bBase) and clazz != EstG3bBase]


class EstG3bBase:
    def __init__(self, country, base_matchers, add_matchers=None, replace_matchers=None) -> None:
        self._holidays = holidays.CountryHoliday(country.upper())
        self._matchers = base_matchers

        if replace_matchers:
            self._matchers = replace_matchers.copy()
        if add_matchers:
            self._machers.extend(add_matchers)

        assert self._matchers

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
        first_minute = next(minutes)
        minutes = itertools.chain([first_minute], minutes)

        matches = []

        for minute in minutes:
            minute_matchers = []

            # find the highest matcher for each group (if any) and save it
            for group in self._matchers:
                try:
                    minute_matchers.append(max([
                        matcher for matcher in group
                        if matcher(minute, first_minute, self._holidays)
                    ]))
                except ValueError:  # no match found
                    pass

            minute_matchers = set(minute_matchers)

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
        )
        super().__init__('DE', matchers, **kwargs)


EstG3bDE = EstG3bGermany
