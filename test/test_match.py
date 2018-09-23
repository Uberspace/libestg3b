import datetime as DT
from decimal import Decimal

import pytest

from libestg3b import Match
from libestg3b.matcher import Matcher


def make_matcher(slug, **kwargs):
    return Matcher(
        'M_' + slug,
        'Matcher',
        lambda m: True,
        **kwargs,
    )


@pytest.fixture
def match():
    return Match(
        DT.datetime(2018, 1, 1, 0),
        DT.datetime(2018, 1, 1, 2, 30),
        [
            make_matcher('m25', multiply=Decimal('0.25')), make_matcher('m5', multiply=Decimal('0.5')),
            make_matcher('a5', add=Decimal(5)), make_matcher('a3', add=Decimal(3)),
        ]
    )


def test_match(match):
    assert match.hours == Decimal('2.5')
    assert match.bonus_multiply == Decimal('0.75')
    assert match.bonus_add == Decimal(8)


def test_match_no_matchers():
    match = Match(DT.datetime(2018, 1, 1, 0), DT.datetime(2018, 1, 1, 2, 30), [])
    assert match.hours == Decimal(2.5)
    assert match.bonus_multiply == Decimal(0)
    assert match.bonus_add == Decimal(0)
