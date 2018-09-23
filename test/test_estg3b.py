import datetime as DT
import itertools
from decimal import Decimal

import pytest

from libestg3b import EStG3b, EStG3bBase, EStG3bs, Match
from libestg3b.matcher import Matcher, MatcherGroup


def _matchers(e, *slugs):
    found = set()
    slugs = set(slugs)

    for matcher in itertools.chain.from_iterable(e._groups):
        if matcher._slug in slugs:
            found.add(matcher)
            slugs.remove(matcher._slug)

    if slugs:
        raise LookupError('Could not find ' + ' '.join(slugs))

    return found


def test_estg3b_invalid_country():
    with pytest.raises(Exception):
        EStG3b('MENOEXISTING')


def test_estg3b():
    assert issubclass(EStG3b('DE'), EStG3bBase)


def test_estg3bs():
    es = EStG3bs()
    assert len(es) == 1
    langs = [e.aliases[0] for e in es]
    assert 'GERMANY' in langs


def test_estg3bbase_list_minutes():
    e = EStG3b('DE')()
    minutes = e._list_minutes(DT.datetime(2018, 10, 1, 5, 10, 13), DT.datetime(2018, 10, 1, 9, 10))
    minutes = list(minutes)
    assert len(minutes) == 4*60
    assert minutes[0] == DT.datetime(2018, 10, 1, 5, 10)
    assert minutes[-1] == DT.datetime(2018, 10, 1, 9, 9)


def test_estg3bbase_list_minutes_wrong_order():
    e = EStG3b('DE')()
    with pytest.raises(Exception):
        list(e._list_minutes(DT.datetime(2018, 10, 1), DT.datetime(2018, 9, 1)))


def test_estg3bbase_calculate_shift():
    e = EStG3b('DE')()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'DE_NIGHT'))


def test_estg3bbase_calculate_shift_multimatch():
    e = EStG3b('DE')()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 7)])
    assert isinstance(match, list)
    assert len(match) == 2
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'DE_NIGHT'))
    assert match[1] == Match(DT.datetime(2018, 2, 1, 6), DT.datetime(2018, 2, 1, 7), set())


def test_estg3bbase_calculate_shift_nomatch():
    e = EStG3b('DE')()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 8), DT.datetime(2018, 2, 1, 9)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 2, 1, 8), DT.datetime(2018, 2, 1, 9), set())


def test_estg3bbase_calculate_shift_sunday_plus_night():
    e = EStG3b('DE')()
    match = e.calculate_shift([DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22), _matchers(e, 'DE_NIGHT', 'DE_SUNDAY'))


def test_estg3bbase_calculate_shifts():
    e = EStG3b('DE')()
    matches = e.calculate_shifts([
        [DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)],
        [DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 7)],
    ])
    matches = list(matches)

    assert len(matches) == 2

    assert len(matches[0]) == 1
    assert matches[0][0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'DE_NIGHT'))

    assert len(matches[1]) == 2
    assert matches[1][0] == Match(DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 6), _matchers(e, 'DE_NIGHT'))
    assert matches[1][1] == Match(DT.datetime(2018, 2, 3, 6), DT.datetime(2018, 2, 3, 7), set())


def test_estg3bbase_add_matchers():
    e = EStG3b('DE')(
        add_matchers=[
            MatcherGroup('SSPECIAL_GRP1', 'One very special group', matchers=[]),
            MatcherGroup('SSPECIAL_GRP2', 'Two very special group', matchers=[]),
        ]
    )

    assert 'SSPECIAL_GRP1' in (g._slug for g in e._groups)
    assert 'SSPECIAL_GRP2' in (g._slug for g in e._groups)


def test_estg3bbase_add_matchers_extend():
    e = EStG3b('DE')(
        add_matchers=[
            MatcherGroup('GRP_DE_NIGHT', '', matchers=[
                Matcher('SPECIAL', 'Special', lambda m: True, multiply=Decimal("1")),
            ]),
        ]
    )

    group = dict((g._slug, g) for g in e._groups)['GRP_DE_NIGHT']
    assert 'SPECIAL' in group


def test_estg3bbase_replace_matchers():
    e = EStG3b('DE')(
        replace_matchers=[
            MatcherGroup('SSPECIAL_GRP', 'One very special group', matchers=[]),
        ]
    )

    assert len(e._groups) == 1
    assert e._groups[0]._slug == 'SSPECIAL_GRP'
