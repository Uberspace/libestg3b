import dataclasses
import datetime
from decimal import Decimal
from inspect import signature
from typing import (Callable, Dict, Iterable, Iterator,  # noqa: W0611
                    Optional, Set)

import dateutil

import holidays


class Matcher():
    """
    Given a work shift, calculate if a defined bonus rule (e.g. "24th of december
    pays 50% more") is to be applied / matches.

    :param slug: a machine and human-ish readable name for this matcher (see below).
    :param description: a human readable short-form description
    :param impl: actual matching function, accepting one, two or three parameters.
    :param multiply: heigth of the bonus, as a factor. Supplying `0.25` results in a pay increase of 25%.
    :param add: heigth of the bonus, as an absolute currency value. Either ``multiply`` or ``add`` must be given, but not both.

    The actual logic of a matcher is passed in via the ``impl`` parameter. This
    function must accept 1-3 arguments: ``minute``, ``start`` and ``holidays``.
    Refer to :meth:`match` for the meaning of those parameters.
    """

    def __init__(self, slug: str, description: str, impl: Callable[..., bool], *, multiply: Optional[Decimal] = None, add: Optional[Decimal] = None, tests=[]) -> None:
        self._slug = slug
        self._description = description
        self._impl = impl
        self._multiply = multiply
        self._add = add
        self._tests = tests

        if multiply is not None and add is None:
            assert isinstance(multiply, Decimal)
            assert multiply > 0
        elif add is not None and multiply is None:
            assert isinstance(add, Decimal)
            assert add > 0
        else:
            assert False, "provide either multiply or add, but not both."

        assert len(slug) > 0
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

    def _examples(self):
        for t in self._tests:
            start, minute = t[0].split('~')
            minute = self._parse_test_time(minute)
            start = self._parse_test_time(start)

            if minute.time() < start.time():
                minute = minute + dateutil.relativedelta.relativedelta(days=1)

            yield [
                minute,
                start,
                t[1],
            ]

    def match(self, minute: datetime.datetime, start: datetime.datetime, holidays: holidays.HolidayBase) -> bool:
        """
        For matching, a shift must be split into its individual minutes. Each of
        these minutes is then passed into this method. Additionally the very first
        minute is provided, to enable rules like (worked after midnight, but
        started before).

        :param minute: current minute to be matched
        :param start: very fist minute in this shift
        :param holidays: holidays in the currently active country (see `python-holidays <https://github.com/dr-prodigy/python-holidays>`_)

        >>> from decimal import Decimal
        >>> import datetime as DT
        >>> from libestg3b.matcher import Matcher
        >>> m = Matcher("NIGHT", "Nachtarbeit", lambda m, f: m.hour >= 20, multiply=Decimal(2))
        # Shift started at 2018-02-02 21:00 and this is the first minute: match!
        >>> m.match(DT.datetime(2018, 2, 2, 21), DT.datetime(2018, 2, 2, 21), None)
        True
        # Shift started at 2018-02-02 20:00 and 21:00 is checked: match!
        >>> m.match(DT.datetime(2018, 2, 2, 21), DT.datetime(2018, 2, 2, 20), None)
        True
        # Shift started at 2018-02-02 18:00 and 19:00 is checked: no match
        >>> m.match(DT.datetime(2018, 2, 2, 19), DT.datetime(2018, 2, 2, 18), None)
        False
        # Shift started at 2018-02-02 23:00 and 01:00 on the following day is checked
        # even though the start of this shift is within the timeframe "after 21:00",
        # the checked minute is not, so we don't match.
        >>> m.match(DT.datetime(2018, 2, 3, 1), DT.datetime(2018, 2, 2, 23), None)
        False
        """
        narg = len(self._impl_parameters)

        if narg == 1:
            r = self._impl(minute)
        elif narg == 2:
            r = self._impl(minute, start)
        elif narg == 3:
            r = self._impl(minute, start, holidays)

        assert isinstance(r, bool)

        return r

    def __repr__(self):
        return f'<Matcher: {self._slug} {self._description}>'

    def __hash__(self):
        return hash(self._slug)

    def __eq__(self, other):
        return self._slug == other._slug

    def __gt__(self, other):
        return self._bonus > other._bonus

    def __lt__(self, other):
        return self._bonus < other._bonus


class DayMatcher(Matcher):
    """
    Match, if the given minute is within the given day. This can be useful to
    increase pay on days, which are not official holidays, but still get a
    special treatment in the law (for example: 31th of December in Germany).

    :param slug: machine-readable name of this matcher, see :class:`Matcher`
    :param month: only match, if shift is within this month, counted from 1 = January
    :param day: only match, if shift is on this day, counted from 1

    Additionally all keyword arguments defined for :class:`Matcher` can be used.

    >>> from decimal import Decimal
    >>> import datetime as DT
    >>> from libestg3b.matcher import DayMatcher
    >>> m = DayMatcher("Helloween", 10, 31, multiply=Decimal("2"))
    >>> m
    <Matcher: Helloween YYYY-10-31>
    >>> m.match(DT.datetime(2018, 10, 31, 13), DT.datetime(2018, 10, 31, 12), None)
    True
    >>> m.match(DT.datetime(2018, 10, 30, 13), DT.datetime(2018, 10, 30, 12), None)
    False
    """
    def __init__(self, slug: str, month: int, day: int, **kwargs) -> None:
        super().__init__(
            slug, f'YYYY-{month:02d}-{day:02d}',
            lambda m: m.month == month and m.day == day,
            **kwargs,
        )


class DayTimeMatcher(Matcher):
    """
    Like :class:`DayMatcher`, but additionally require the shift to be after a certain time.

    :param slug: machine-readable name of this matcher, see :class:`Matcher`
    :param month: only match, if shift is within this month, counted from 1 = January
    :param day: only match, if shift is on this day, counted from 1
    :param hour: only match, if shift is after or in this hour. Supplying ``14`` results in ``14:00`` to ``24:00`` to be matched.

    Additionally all keyword arguments defined for :class:`Matcher` can be used.

    >>> from decimal import Decimal
    >>> import datetime as DT
    >>> from libestg3b.matcher import DayTimeMatcher
    >>> m = DayTimeMatcher("NEWYEARSEVE", 12, 31, 14, multiply=Decimal("1"))
    >>> m
    <Matcher: NEWYEARSEVE YYYY-12-31 14:00+>
    >>> m.match(DT.datetime(2018, 12, 31, 13), DT.datetime(2018,12, 31, 13), None)
    False
    >>> m.match(DT.datetime(2018, 12, 31, 14), DT.datetime(2018,12, 31, 14), None)
    True
    """
    def __init__(self, slug: str, month: int, day: int, hour: int, **kwargs) -> None:
        super().__init__(
            slug, f'YYYY-{month:02d}-{day:02d} {hour:02d}:00+',
            lambda m: m.month == month and m.day == day and m.hour >= hour,
            **kwargs,
        )


class MatcherGroup():
    """
    A collection of similar :class:`Matcher` instances. When the group is evaluated, only the highest matching machter is returned.

    :param description: a short, human-readable text, explaining why the given matchers are grouped together.
    :param matchers: the initial set of matchers.
    """
    def __init__(self, description: str, matchers: Iterable[Matcher]) -> None:
        self._description = description
        self._matchers = {}  # type: Dict[str, Matcher]
        self.extend(matchers)

    def append(self, matcher: Matcher, replace: bool = False) -> None:
        """
        :param matcher: matcher to add; it must not yet exist in the group.
        :param replace: if matcher duplicates an existing one, overwrite it.
        """
        if matcher._slug in self._matchers and not replace:
            raise Exception(f'Slug {matcher._slug} is already in this group')
        if not isinstance(matcher, Matcher):
            raise Exception('Matchers must be derived from libestg3b.Matcher')

        self._matchers[matcher._slug] = matcher

    def match(self, minute: datetime.datetime, start: datetime.datetime, holidays: holidays.HolidayBase) -> Optional[Matcher]:
        """
        Evaluate this group. The given shift is tested using each of the stored
        matchers. The matcher with the highest bonus is the returned. If not a
        single one matches, ``None`` is returned.

        This method is normally used by :class:`libestg3b.EstG3b`, but you can
        use it to implement more complex scenarios yourself.

        :param minute: minute to evaluate (see :class:`libestgb3.EstG3b`)
        :param start: the first minute in this shift  (see :class:`libestgb3.EstG3b`)
        """
        try:
            return max(filter(lambda matcher: matcher.match(minute, start, holidays), self))
        except ValueError:  # no match found
            return None

    def extend(self, matchers: Iterable[Matcher], replace: bool = False) -> None:
        """
        Add the given matchers to this group.

        :param matchers:
        :param replace: if one of the given matcher duplicates an existing one, overwrite it instead of raising an exception.
        """
        for m in matchers:
            self.append(m, replace)

    def __contains__(self, item) -> bool:
        if isinstance(item, Matcher):
            return item._slug in self._matchers
        else:
            return item in self._matchers

    def __iter__(self) -> Iterator[Matcher]:
        return self._matchers.values().__iter__()


@dataclasses.dataclass
class Match():
    start: datetime.datetime
    end: datetime.datetime
    matchers: Set[Matcher]
