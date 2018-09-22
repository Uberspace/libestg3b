import datetime
import inspect
import itertools
from decimal import Decimal
from typing import Iterator, List, Set, Tuple, Type

from dateutil.relativedelta import relativedelta

import dataclasses
import holidays

from .matcher import DayMatcher, DayTimeMatcher
from .matcher import Matcher as M
from .matcher import MatcherGroup

from .matcher import Matcher  # isort:skip


class EStG3bBase:
    def __init__(self, country, groups, add_matchers=None, replace_matchers=None) -> None:
        self._holidays = holidays.CountryHoliday(country.upper())
        self._groups = list(groups)

        if replace_matchers:
            self._groups = replace_matchers.copy()

        if add_matchers:
            old_grps = dict((g._slug, g) for g in self._groups)
            for new_grp in add_matchers:
                if new_grp._slug in old_grps:
                    old_grps[new_grp._slug].extend(new_grp, replace=True)
                else:
                    self._groups.append(new_grp)

        assert self._groups
        assert all(lambda g: isinstance(g, MatcherGroup) for g in self._groups)

    def _list_minutes(self, start: datetime.datetime, end: datetime.datetime) -> Iterator[datetime.datetime]:
        assert start < end

        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)

        while start < end:
            yield start
            start = start + relativedelta(minutes=1)

    def calculate_shift(self, shift: Tuple[datetime.datetime, datetime.datetime]) -> List["Match"]:
        """
        Turn a shift into a number of matches, containing the relevant Matchers (if any),
        which can be used to calculate the appropriate high of bonus payments.

        >>> import datetime as DT
        >>> from libestg3b import EStG3b
        >>> e = EStG3b("DE")
        >>> e.calculate_shift([DT.datetime(2018, 12, 24, 13), DT.datetime(2018, 12, 25, 2)])
        [
            Match(start=datetime.datetime(2018, 12, 24, 13, 0), end=datetime.datetime(2018, 12, 24, 14, 0), matchers=set(
            )),
            Match(start=datetime.datetime(2018, 12, 24, 14, 0), end=datetime.datetime(2018, 12, 24, 20, 0), matchers={
                <Matcher: DE_HEILIGABEND YYYY-12-24 14:00+>
            }),
            Match(start=datetime.datetime(2018, 12, 24, 20, 0), end=datetime.datetime(2018, 12, 25, 0, 0), matchers={
                <Matcher: DE_HEILIGABEND YYYY-12-24 14:00+>,
                <Matcher: DE_NIGHT Nachtarbeit 20:00-06:00>
            }),
            Match(start=datetime.datetime(2018, 12, 25, 0, 0), end=datetime.datetime(2018, 12, 25, 2, 0), matchers={
                <Matcher: DE_WEIHNACHTSFEIERTAG_1 YYYY-12-25>,
                <Matcher: DE_NIGHT_00_04 Nachtarbeit 00:00-04:00 (Folgetag)>
            })
        ]

        :param shift: a `(starttime, endtime)` tuple. Describes a shift started and `starttime` (inclusive) and ending at `endtime` (exclusive).
        """
        assert len(shift) == 2
        assert isinstance(shift[0], datetime.datetime)
        assert isinstance(shift[1], datetime.datetime)

        minutes = self._list_minutes(shift[0], shift[1])
        start = next(minutes)
        minutes = itertools.chain([start], minutes)

        matches = []  # type: List[Match]

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

    def calculate_shifts(self, shifts: List[Tuple[datetime.datetime, datetime.datetime]]) -> Iterator[List["Match"]]:
        """
        Behaves just like :meth:`calculate_shift`, but takes a list of shifts and returns a list of list of matches.

        :param shifts:
        """
        return map(self.calculate_shift, shifts)


def EStG3b(country: str) -> Type[EStG3bBase]:
    """
    Get the implementation class for the given country.

    :param country: ISO short code of the desired country, e.g. ``"DE"``
    """
    try:
        country_estg3b = globals()['EStG3b' + country]
    except (KeyError):
        raise KeyError("Country %s not available" % country)
    return country_estg3b


def EStG3bs() -> List[Type[EStG3bBase]]:
    """
    Get a list containing implementation classes for all implemented countries.
    """
    return [
        clazz
        for clazz in globals().values()
        if inspect.isclass(clazz) and issubclass(clazz, EStG3bBase) and clazz != EStG3bBase
    ]


@dataclasses.dataclass
class Match():
    """
    The final result of the calculation process. It links time worked to additional
    payments (or the information that none are relevant).

    :param start: the (inclusive) time this shift part starts at
    :param end: the (exclusive) time this shift part ends at
    :param matchers: all the relevant Matcher instances. May be empty to indicate, that no match has been found.
    """
    start: datetime.datetime
    end: datetime.datetime
    matchers: Set[Matcher]


class EStG3bGermany(EStG3bBase):
    def __init__(self, **kwargs):
        matchers = (
            MatcherGroup('GRP_DE_NIGHT', 'Nachtarbeit', (
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
            MatcherGroup('GRP_HOLIDAYS', 'Sonntags und Feiertagsarbeit', (
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
                DayTimeMatcher('DE_HEILIGABEND', 12, 24, 14, multiply=Decimal('1.25')),
                DayTimeMatcher('DE_SILVESTER', 12, 31, 14, multiply=Decimal('1.25')),
                DayMatcher('DE_WEIHNACHTSFEIERTAG_1', 12, 25, multiply=Decimal('1.5')),
                DayMatcher('DE_WEIHNACHTSFEIERTAG_2', 12, 26, multiply=Decimal('1.5')),
                DayMatcher('DE_TAGDERARBEIT', 5, 1, multiply=Decimal('1.5')),
            )),
        )
        super().__init__('DE', matchers, **kwargs)


EStG3bDE = EStG3bGermany
