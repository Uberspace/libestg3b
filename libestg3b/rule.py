import datetime
from decimal import Decimal
from inspect import signature
from typing import (Callable, Dict, Iterable, Iterator,  # noqa: W0611
                    Optional, Set)

import dateutil
import holidays


class Rule():
    """
    Defines a situation in which an employee might receive extra pay, e.g.
    "on 24th of december, pay 50% more".

    :param slug: a machine and human-ish readable name for this rule (see below).
    :param description: a human readable short-form description
    :param impl: actual matching function, accepting one, two or three parameters.
    :param multiply: heigth of the bonus, as a factor. Supplying `0.25` results in a pay increase of 25%.
    :param add: heigth of the bonus, as an absolute currency value. Either ``multiply`` or ``add`` must be given, but not both.

    The actual logic of a rule is passed in via the ``impl`` parameter. This
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
        if self._multiply:
            return ('multiply', self._multiply)
        if self._add:
            return ('add', self._add)

        assert False

    def _parse_test_time(self, tt):
        default = datetime.datetime(2018, 1, 10)
        return dateutil.parser.parse(tt, default=default) if tt else default

    def _examples(self):
        for t in self._tests:
            start, minute = t[0].split('~')
            minute = self._parse_test_time(minute)
            start = self._parse_test_time(start)

            if minute.time() < start.time():
                minute = minute + datetime.timedelta(days=1)

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

        >>> from decimal import Decimal
        >>> import datetime as DT
        >>> from libestg3b.rule import Rule
        >>> m = Rule("NIGHT", "Nachtarbeit", lambda m, f: m.hour >= 20, multiply=Decimal(2))
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

        :param minute: current minute to be matched
        :param start: very fist minute in this shift
        :param holidays: holidays in the currently active country (see `python-holidays <https://github.com/dr-prodigy/python-holidays>`_)
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
        return f'<Rule: {self._slug} {self._description}>'

    def __hash__(self):
        return hash(self._slug)

    def __eq__(self, other):
        return self._slug == other._slug

    def __gt__(self, other):
        if self._bonus[0] != other._bonus[0]:
            raise Exception("cannot compare multiply to add rules")
        return self._bonus > other._bonus

    def __lt__(self, other):
        if self._bonus[0] != other._bonus[0]:
            raise Exception("cannot compare multiply to add rules")
        return self._bonus < other._bonus


class DayRule(Rule):
    """
    Match, if the given minute is within the given day. This can be useful to
    increase pay on days, which are not official holidays, but still get a
    special treatment in the law (for example: 31th of December in Germany).

    >>> from decimal import Decimal
    >>> import datetime as DT
    >>> from libestg3b.rule import DayRule
    >>> m = DayRule("Helloween", 10, 31, multiply=Decimal("2"))
    >>> m
    <Rule: Helloween YYYY-10-31>
    >>> m.match(DT.datetime(2018, 10, 31, 13), DT.datetime(2018, 10, 31, 12), None)
    True
    >>> m.match(DT.datetime(2018, 10, 30, 13), DT.datetime(2018, 10, 30, 12), None)
    False

    :param slug: machine-readable name of this rule, see :class:`Rule`
    :param month: only match, if shift is within this month, counted from 1 = January
    :param day: only match, if shift is on this day, counted from 1

    Additionally all keyword arguments defined for :class:`Rule` can be used.
    """
    def __init__(self, slug: str, month: int, day: int, **kwargs) -> None:
        super().__init__(
            slug, f'YYYY-{month:02d}-{day:02d}',
            lambda m: m.month == month and m.day == day,
            **kwargs,
        )


class DayTimeRule(Rule):
    """
    Like :class:`DayRule`, but additionally require the shift to be after a certain time.

    >>> from decimal import Decimal
    >>> import datetime as DT
    >>> from libestg3b.rule import DayTimeRule
    >>> m = DayTimeRule("NEWYEARSEVE", 12, 31, 14, multiply=Decimal("1"))
    >>> m
    <Rule: NEWYEARSEVE YYYY-12-31 14:00+>
    >>> m.match(DT.datetime(2018, 12, 31, 13), DT.datetime(2018,12, 31, 13), None)
    False
    >>> m.match(DT.datetime(2018, 12, 31, 14), DT.datetime(2018,12, 31, 14), None)
    True

    :param slug: machine-readable name of this rule, see :class:`Rule`
    :param month: only match, if shift is within this month, counted from 1 = January
    :param day: only match, if shift is on this day, counted from 1
    :param hour: only match, if shift is after or in this hour. Supplying ``14`` results in ``14:00`` to ``24:00`` to be matched.

    Additionally all keyword arguments defined for :class:`Rule` can be used.
    """
    def __init__(self, slug: str, month: int, day: int, hour: int, **kwargs) -> None:
        super().__init__(
            slug, f'YYYY-{month:02d}-{day:02d} {hour:02d}:00+',
            lambda m: m.month == month and m.day == day and m.hour >= hour,
            **kwargs,
        )


class RuleGroup():
    """
    A collection of similar :class:`Rule` instances. When the group is evaluated, only the highest matching machter is returned.

    :param slug: a machine and human-ish readable name for this rule, must not change.
    :param description: a short, human-readable text, explaining why the given rules are grouped together.
    :param rules: the initial set of rules.
    """
    def __init__(self, slug: str, description: str, rules: Iterable[Rule]) -> None:
        self._slug = slug
        self._description = description
        self._rules = {}  # type: Dict[str, Rule]
        self.extend(rules)

    def append(self, rule: Rule, replace: bool = False) -> None:
        """
        :param rule: rule to add; it must not yet exist in the group.
        :param replace: if rule duplicates an existing one, overwrite it.
        """
        if not isinstance(rule, Rule):
            raise Exception('Rules must be derived from libestg3b.Rule')
        if rule._slug in self._rules and not replace:
            raise Exception(f'Slug {rule._slug} is already in this group')

        if self._rules:
            my_type = next(iter(self._rules.values()))._bonus[0]
            if my_type != rule._bonus[0]:
                raise Exception(f'cannot add a {rule._bonus[0]} rule to a group containing {my_type} rules.')

        self._rules[rule._slug] = rule

    def match(self, minute: datetime.datetime, start: datetime.datetime, holidays: holidays.HolidayBase) -> Optional[Rule]:
        """
        Evaluate this group. The given shift is tested using each of the stored
        rules. The rule with the highest bonus is the returned. If not a
        single one matches, ``None`` is returned.

        This method is normally used by :class:`libestg3b.EStG3b`, but you can
        use it to implement more complex scenarios yourself.

        :param minute: minute to evaluate (see :class:`libestgb3.EStG3b`)
        :param start: the first minute in this shift  (see :class:`libestgb3.EStG3b`)
        """
        try:
            return max(filter(lambda rule: rule.match(minute, start, holidays), self))
        except ValueError:  # no match found
            return None

    def extend(self, rules: Iterable[Rule], replace: bool = False) -> None:
        """
        Add the given rules to this group.

        :param rules:
        :param replace: if one of the given rule duplicates an existing one, overwrite it instead of raising an exception.
        """
        for m in rules:
            self.append(m, replace)

    def __contains__(self, item) -> bool:
        if isinstance(item, Rule):
            return item._slug in self._rules
        else:
            return item in self._rules

    def __iter__(self) -> Iterator[Rule]:
        return self._rules.values().__iter__()
