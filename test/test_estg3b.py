import datetime as DT
from libestg3b import EstG3b
from libestg3b.matcher import Match


def test_estg3b():
    e = EstG3b()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 2), DT.datetime(2018, 2, 1, 5, 1)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert isinstance(match[0], Match)
    assert match[0].start == DT.datetime(2018, 2, 1, 2)
    assert match[0].end == DT.datetime(2018, 2, 1, 5)
    assert len(match[0].matchers) == 1
    assert match[0].matchers[0]._description == 'Nachtarbeit 20:00-06:00'


def test_estg3b_nomatch():
    e = EstG3b()
    match = e.calculate_shift([DT.datetime(2018, 2, 1, 8), DT.datetime(2018, 2, 1, 9, 1)])
    assert isinstance(match, list)
    assert len(match) == 1
    assert isinstance(match[0], Match)
    assert match[0].start == DT.datetime(2018, 2, 1, 8)
    assert match[0].end == DT.datetime(2018, 2, 1, 9)
    assert len(match[0].matchers) == 0
