import dataclasses  # isort:skip
import datetime
import itertools
from decimal import Decimal
from typing import Iterator, List, Set, Tuple

import holidays

from .rule import RuleGroup

from .rule import Rule  # isort:skip


class EStG3bBase:
    def __init__(self, country, groups, add_rules=None, replace_rules=None) -> None:
        self._holidays = holidays.CountryHoliday(country.upper())
        self._groups = list(groups)

        if replace_rules:
            self._groups = replace_rules.copy()

        if add_rules:
            old_grps = dict((g._slug, g) for g in self._groups)
            for new_grp in add_rules:
                if new_grp._slug in old_grps:
                    old_grps[new_grp._slug].extend(new_grp, replace=True)
                else:
                    self._groups.append(new_grp)

        assert self._groups
        assert all(lambda g: isinstance(g, RuleGroup) for g in self._groups)

    def _list_minutes(self, start: datetime.datetime, end: datetime.datetime) -> Iterator[datetime.datetime]:
        assert start < end

        start = start.replace(second=0, microsecond=0)
        end = end.replace(second=0, microsecond=0)

        while start < end:
            yield start
            start = start + datetime.timedelta(minutes=1)

    def calculate_shift(self, shift: Tuple[datetime.datetime, datetime.datetime]) -> List["Match"]:
        """
        Turn a shift into a number of matches, containing the relevant rules (if any),
        which can be used to calculate the appropriate high of bonus payments.

        >>> import datetime as DT
        >>> from libestg3b import EStG3b
        >>> e = EStG3b("DE")
        >>> e.calculate_shift([DT.datetime(2018, 12, 24, 13), DT.datetime(2018, 12, 25, 2)])
        [
            Match(start=datetime.datetime(2018, 12, 24, 13, 0), end=datetime.datetime(2018, 12, 24, 14, 0), rules=set(
            )),
            Match(start=datetime.datetime(2018, 12, 24, 14, 0), end=datetime.datetime(2018, 12, 24, 20, 0), rules={
                <Rule: DE_HEILIGABEND YYYY-12-24 14:00+>
            }),
            Match(start=datetime.datetime(2018, 12, 24, 20, 0), end=datetime.datetime(2018, 12, 25, 0, 0), rules={
                <Rule: DE_HEILIGABEND YYYY-12-24 14:00+>,
                <Rule: DE_NIGHT Nachtarbeit 20:00-06:00>
            }),
            Match(start=datetime.datetime(2018, 12, 25, 0, 0), end=datetime.datetime(2018, 12, 25, 2, 0), rules={
                <Rule: DE_WEIHNACHTSFEIERTAG_1 YYYY-12-25>,
                <Rule: DE_NIGHT_START_YESTERDAY Nachtarbeit 00:00-04:00 (Folgetag)>
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
            minute_rules = set(
                group.match(minute, start, self._holidays)
                for group in self._groups
            )
            minute_rules.discard(None)

            if matches and matches[-1].rules == minute_rules:
                # combine equal matches by increasing the length of the last one
                matches[-1].end = matches[-1].end + datetime.timedelta(minutes=1)
            else:
                # a list of minutes is inclusive the last one, the `end` stamp is exclusive
                matches.append(Match(minute, minute + datetime.timedelta(minutes=1), minute_rules))

        return matches

    def calculate_shifts(self, shifts: List[Tuple[datetime.datetime, datetime.datetime]]) -> Iterator[List["Match"]]:
        """
        Behaves just like :meth:`calculate_shift`, but takes a list of shifts and returns a list of list of matches.

        :param shifts:
        """
        return map(self.calculate_shift, shifts)


@dataclasses.dataclass
class Match():
    """
    The final result of the calculation process. It links time worked to additional
    payments (or the information that none are relevant).

    :param start: the (inclusive) time this shift part starts at
    :param end: the (exclusive) time this shift part ends at
    :param rules: all the relevant Rule instances. May be empty to indicate, that no match has been found.
    """
    start: datetime.datetime
    end: datetime.datetime
    rules: Set[Rule]

    def __repr__(self):
        return f'<Match {self.start.isoformat()}~{self.end.isoformat()}, {self.rules_str}, add={self.bonus_add}, multiply={self.bonus_multiply}>'

    def _sum_bonus(self, t):
        return sum(m._bonus[1] for m in self.rules if m._bonus[0] == t)

    @property
    def rules_str(self) -> str:
        """ a human-readable representation of all the rules matched, e.g. ``DE_NIGHT+DE_SUNDAY`` """
        if self.rules:
            return '+'.join(m._slug for m in self.rules)
        else:
            return 'None'

    @property
    def bonus_multiply(self) -> Decimal:
        """ the height of the bonus, as a factor to add e.g. ``Decimal(0.2)`` => 20%. """
        return self._sum_bonus('multiply')

    @property
    def bonus_add(self) -> Decimal:
        """ the total amount of monetary units to add as a bonus, e.g. ``Decimal(5)`` => 5€. """
        return self._sum_bonus('add')

    @property
    def hours(self) -> Decimal:
        """ the number of hours this Match covers, e.g. ``Decimal(1.5)`` """
        return Decimal((self.end - self.start).seconds) / 60 / 60
