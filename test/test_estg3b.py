import datetime as DT
import itertools

from libestg3b import EstG3b, Match


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


def test_estg3b():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'DE_NIGHT'))


def test_estg3b_multimatch():
    e = EstG3b('DE')
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 7)])
    assert isinstance(match, list)
    assert len(match) == 2
    assert match[0] == Match(DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 6), _matchers(e, 'DE_NIGHT'))
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
    assert match[0] == Match(DT.datetime(2018, 9, 16, 20), DT.datetime(2018, 9, 16, 22), _matchers(e, 'DE_NIGHT', 'DE_SUNDAY'))
