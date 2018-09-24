import itertools

import pytest

from libestg3b import EStG3bs


def _generate_rule_examples(e):
    for m in itertools.chain.from_iterable(e._groups):  # flatten groups
        yield from ([m, e._holidays, *ex] for ex in m._examples())


@pytest.mark.parametrize(
    'rule,holidays,minute,start,result',
    itertools.chain.from_iterable(_generate_rule_examples(e()) for e in EStG3bs())
)
def test_rules(rule, minute, start, holidays, result):
    assert rule.match(minute, start, holidays) == result
