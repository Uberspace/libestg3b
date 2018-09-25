import datetime as DT
from decimal import Decimal

import pytest

from libestg3b import Match
from libestg3b.rule import Rule


def make_rule(slug, **kwargs):
    return Rule(
        'R_' + slug,
        'Rule',
        lambda m: True,
        **kwargs,
    )


@pytest.fixture
def match():
    return Match(
        DT.datetime(2018, 1, 1, 0),
        DT.datetime(2018, 1, 1, 2, 30),
        [
            make_rule('m25', multiply=Decimal('0.25')), make_rule('m5', multiply=Decimal('0.5')),
            make_rule('a5', add=Decimal(5)), make_rule('a3', add=Decimal(3)),
        ]
    )


def test_match(match):
    assert match.minutes == Decimal('150')
    assert match.bonus_multiply == Decimal('0.75')
    assert match.bonus_add == Decimal(8)


def test_match_no_rules():
    match = Match(DT.datetime(2018, 1, 1, 0), DT.datetime(2018, 1, 1, 2, 30), [])
    assert match.minutes == Decimal('150')
    assert match.bonus_multiply == Decimal(0)
    assert match.bonus_add == Decimal(0)
