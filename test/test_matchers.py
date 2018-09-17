import itertools

import holidays
import pytest

from libestg3b.matcher import matchers


def _generate_matcher_examples(matchers, holidays):
    for m in itertools.chain.from_iterable(matchers):  # flatten groups
        yield from ([m, holidays, *ex] for ex in m.examples())


@pytest.mark.parametrize(
    'matcher,holidays,minute,first_minute,result',
    _generate_matcher_examples(matchers['DE'], holidays.DE())
)
def test_matchers(matcher, minute, first_minute, holidays, result):
    assert matcher(minute, first_minute, holidays) == result
