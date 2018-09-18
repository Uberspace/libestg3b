import itertools

import pytest

from libestg3b.estg3b import EstG3bs


def _generate_matcher_examples(e):
    for m in itertools.chain.from_iterable(e._matchers):  # flatten groups
        yield from ([m, e._holidays, *ex] for ex in m.examples())


@pytest.mark.parametrize(
    'matcher,holidays,minute,first_minute,result',
    itertools.chain.from_iterable(_generate_matcher_examples(e()) for e in EstG3bs())
)
def test_matchers(matcher, minute, first_minute, holidays, result):
    assert matcher(minute, first_minute, holidays) == result
