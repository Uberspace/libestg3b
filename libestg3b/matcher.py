import dataclasses
import datetime
from decimal import Decimal
from inspect import signature
from typing import Dict, Iterable, Iterator, Optional, Set  # noqa: W0611

import dateutil
import holidays


class Matcher():
    """ Defines a bonus rule, e.g. "if someone works between 8pm and 6am, give them 25% more" """

    def __init__(self, slug, description: str, impl, *, multiply: Optional[Decimal] = None, add: Optional[Decimal] = None, tests=[]) -> None:
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
    """ match, if the given minute is within the given day. Keyword arguments are passed onto Matcher. """
    def __init__(self, slug: str, month: int, day: int, **kwargs) -> None:
        super().__init__(
            slug, f'YYYY-{month:02d}-{day:02d}',
            lambda m: m.month == month and m.day == day,
            **kwargs,
        )


class DayTimeMatcher(Matcher):
    """ match, if the given minute is within the given day after the given hour. Keyword arguments are passed onto Matcher. """
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

        for m in matchers:
            self.append(m)

    def append(self, matcher: Matcher) -> None:
        """
        :param matcher: matcher to add; it must not yet exist in the group.
        """
        if matcher._slug in self._matchers:
            raise Exception(f'Slug {matcher._slug} is already in this group')
        if not isinstance(matcher, Matcher):
            raise Exception('Matchers must be derived from libestg3b.Matcher')

        self._matchers[matcher._slug] = matcher

    def match(self, minute: datetime.datetime, start: datetime.datetime, holidays: holidays.HolidayBase) -> Optional[Matcher]:
        """
        Evaluate this group. The given shift is tested using each of the stored
        matchers. The matcher with the highest bonus is the returned. If not a
        single one matches, ``None`` is returned.

        This method is to be used by :class:`libestg3b.EstG3b` only, but you can
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
            if replace:
                self._matchers.pop(m._slug, None)

            self.append(m)

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
