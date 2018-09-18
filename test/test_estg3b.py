import datetime as DT
import itertools

from libestg3b import EstG3b
from libestg3b.matcher import Match


def _matchers(e, *descriptions):
    found = set()
    descriptions = set(descriptions)

    for matcher in itertools.chain.from_iterable(e._matchers):
        if matcher._description in descriptions:
            found.add(matcher)
            descriptions.remove(matcher._description)

    if descriptions:
        raise LookupError('Could not find ' + ','.join(descriptions))

    return found


def test_estg3b():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'Nachtarbeit 20:00-06:00'))


def test_estg3b_multimatch():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 7)])
    assert isinstance(match, list)
    assert len(match) == 2
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'Nachtarbeit 20:00-06:00'))
    assert match[1] == Match(DT.datetime(2018, 2, 1, 6), DT.datetime(2018, 2, 1, 7), set())


def test_estg3b_nomatch():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 8), DT.datetime(2018, 2, 1, 9)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 2, 1, 8), DT.datetime(2018, 2, 1, 9), set())


def test_estg3b_sunday_plus_night():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22), _matchers(e, 'Nachtarbeit 20:00-06:00', 'Sonntagsarbeit'))
