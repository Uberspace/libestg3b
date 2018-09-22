import itertools

import pytest

from libestg3b.estg3b import EStG3bs


def _generate_matcher_examples(e):
    for m in itertools.chain.from_iterable(e._groups):  # flatten groups
        yield from ([m, e._holidays, *ex] for ex in m._examples())


@pytest.mark.parametrize(
    'matcher,holidays,minute,start,result',
    itertools.chain.from_iterable(_generate_matcher_examples(e()) for e in EStG3bs())
)
def test_matchers(matcher, minute, start, holidays, result):
    assert matcher.match(minute, start, holidays) == result
