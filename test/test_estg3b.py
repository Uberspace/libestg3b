import datetime as DT
import itertools
from decimal import Decimal

import pytest

from libestg3b import EStG3b, EStG3bBase, EStG3bs, Match
from libestg3b.rule import Rule, RuleGroup


def _rules(e, *slugs):
    found = set()
    slugs = set(slugs)

    for rule in itertools.chain.from_iterable(e._groups):
        if rule._slug in slugs:
            found.add(rule)
            slugs.remove(rule._slug)

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
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _rules(e, 'DE_NIGHT'))


def test_estg3bbase_calculate_shift_multimatch():
    e = EStG3b('DE')()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 7)])
    assert isinstance(match, list)
    assert len(match) == 2
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _rules(e, 'DE_NIGHT'))
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
    assert match[0] == Match(DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22), _rules(e, 'DE_NIGHT', 'DE_SUNDAY'))


def test_estg3bbase_calculate_shifts():
    e = EStG3b('DE')()
    matches = e.calculate_shifts([
        [DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)],
        [DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 7)],
    ])

    assert len(matches) == 3

    assert matches[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _rules(e, 'DE_NIGHT'))
    assert matches[1] == Match(DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 6), _rules(e, 'DE_NIGHT'))
    assert matches[2] == Match(DT.datetime(2018, 2, 3, 6), DT.datetime(2018, 2, 3, 7), set())


def test_estg3bbase_calculate_shifts_overlapping():
    e = EStG3b('DE')()
    matches = e.calculate_shifts([
        [DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)],
        [DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 7)],
        [DT.datetime(2018, 2, 1, 1), DT.datetime(2018, 2, 1, 2)],
    ])
    # <Match 2018-02-03T02:00:00~2018-02-03T07:00:00, None, add=0, multiply=0>
    # <Match 2018-02-03T06:00:00~2018-02-03T07:00:00, None, add=0, multiply=0>

    assert len(matches) == 3

    assert matches[0] == Match(DT.datetime(2018, 2, 1, 1), DT.datetime(2018, 2, 1, 6), _rules(e, 'DE_NIGHT'))
    assert matches[1] == Match(DT.datetime(2018, 2, 3, 2), DT.datetime(2018, 2, 3, 6), _rules(e, 'DE_NIGHT'))
    assert matches[2] == Match(DT.datetime(2018, 2, 3, 6), DT.datetime(2018, 2, 3, 7), set())


def test_estg3bbase_add_rules():
    e = EStG3b('DE')(
        add_rules=[
            RuleGroup('SSPECIAL_GRP1', 'One very special group', rules=[]),
            RuleGroup('SSPECIAL_GRP2', 'Two very special group', rules=[]),
        ]
    )

    assert 'SSPECIAL_GRP1' in (g._slug for g in e._groups)
    assert 'SSPECIAL_GRP2' in (g._slug for g in e._groups)


def test_estg3bbase_add_rules_extend():
    e = EStG3b('DE')(
        add_rules=[
            RuleGroup('GRP_DE_NIGHT', '', rules=[
                Rule('SPECIAL', 'Special', lambda m: True, multiply=Decimal("1")),
            ]),
        ]
    )

    group = dict((g._slug, g) for g in e._groups)['GRP_DE_NIGHT']
    assert 'SPECIAL' in group


def test_estg3bbase_replace_rules():
    e = EStG3b('DE')(
        replace_rules=[
            RuleGroup('SSPECIAL_GRP', 'One very special group', rules=[]),
        ]
    )

    assert len(e._groups) == 1
    assert e._groups[0]._slug == 'SSPECIAL_GRP'
