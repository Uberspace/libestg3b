import datetime as DT

import pytest

from libestg3b.estg3b import Timespan


@pytest.mark.parametrize("t1,t2,overlaps", [
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 3, 5), DT.datetime(2018, 10, 3, 8)),
        False,
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        True,
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 8), DT.datetime(2018, 10, 2, 9)),
        True,
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 7), DT.datetime(2018, 10, 2, 9)),
        True,
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10)),
        False,
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10)),
        False,
    ],
])
def test_timespan_overlaps(t1, t2, overlaps):
    assert t1.overlaps(t2) == overlaps
    assert t2.overlaps(t1) == overlaps


@pytest.mark.parametrize("t1,t2,tr", [
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 8), DT.datetime(2018, 10, 2, 10)),
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 10)),
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 7), DT.datetime(2018, 10, 2, 10)),
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 10)),
    ],
    [
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        Timespan(DT.datetime(2018, 10, 2, 6), DT.datetime(2018, 10, 2, 7)),
        Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
    ],
])
def test_timespan_merge_with(t1, t2, tr):
    assert t1.merge_with(t2) == tr
    assert t2.merge_with(t1) == tr


def test_timespan_merge_with_non_overlapping():
    t1 = Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8))
    t2 = Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10))

    with pytest.raises(Exception) as exc:
        t1.merge_with(t2)

    assert 'overlapping' in str(exc)


@pytest.mark.parametrize("ts_in,ts_out", [
    [
        [
            Timespan(DT.datetime(2018, 10, 2, 8), DT.datetime(2018, 10, 2, 10)),
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
        ],
        [
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 10)),
        ]
    ],
    [
        [
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
            Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10)),
        ],
        [
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
            Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10)),
        ]
    ],
    [
        [
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 8)),
            Timespan(DT.datetime(2018, 10, 2, 9), DT.datetime(2018, 10, 2, 10)),
            Timespan(DT.datetime(2018, 10, 2, 8), DT.datetime(2018, 10, 2, 9)),
            Timespan(DT.datetime(2018, 10, 2, 11), DT.datetime(2018, 10, 2, 12)),
        ],
        [
            Timespan(DT.datetime(2018, 10, 2, 5), DT.datetime(2018, 10, 2, 10)),
            Timespan(DT.datetime(2018, 10, 2, 11), DT.datetime(2018, 10, 2, 12)),
        ]
    ],
])
def test_timespan_union(ts_in, ts_out):
    assert Timespan.union(ts_in) == ts_out
