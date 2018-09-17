import datetime
from decimal import Decimal
import itertools

import pytest

from libestg3b.matcher import Matcher, DayTimeMatcher, DayMatcher


def test_matcher_init():
    m = Matcher('a', lambda x: False)
    m(None, None, None)


def test_matcher_init_no_description():
    with pytest.raises(AssertionError):
        m = Matcher('', lambda x: False)


@pytest.mark.parametrize("impl", [
    lambda: False,
    lambda a, b, c, d: False,
])
def test_matcher_init_impl_nargs_crash(impl):
    with pytest.raises(AssertionError):
        m = Matcher('a', impl)


@pytest.mark.parametrize("impl", [
    lambda a: False,
    lambda a: True,
])
def test_matcher_call_rtn_type(impl):
    m = Matcher('a', impl)
    m(None, None, None)


def test_matcher_call_rtn_type_crash():
    m = Matcher('a', lambda x: None)
    with pytest.raises(AssertionError):
        m(None, None, None)


def test_matcher_call_passing_1():
    args = None
    def impl(a):
        nonlocal args
        args = [a]
        return True
    m = Matcher('a', impl)
    m(0, 1, 2)
    assert args == [0]


def test_matcher_call_passing_2():
    args = None
    def impl(a, b):
        nonlocal args
        args = [a, b]
        return True
    m = Matcher('a', impl)
    m(0, 1, 2)
    assert args == [0, 1]


def test_matcher_call_passing_3():
    args = None
    def impl(a, b, c):
        nonlocal args
        args = [a, b, c]
        return True
    m = Matcher('a', impl)
    m(0, 1, 2)
    assert args == [0, 1, 2]


@pytest.mark.parametrize('dt,res', [
    (datetime.datetime(2018, 12, 25, 23, 59), False),
    (datetime.datetime(2018, 12, 26, 0), True),
    (datetime.datetime(2018, 12, 26, 23, 59), True),
    (datetime.datetime(2018, 12, 27, 0), False),
    (datetime.datetime(2019, 12, 26, 0), True),
])
def test_daymatcher(dt, res):
    m = DayMatcher(12, 26, multiply=Decimal('1.25'))
    assert m(dt, dt, None) == res


@pytest.mark.parametrize('dt,res', [
    (datetime.datetime(2018, 12, 24, 0), False),
    (datetime.datetime(2018, 12, 24, 13, 59), False),
    (datetime.datetime(2018, 12, 24, 14), True),
    (datetime.datetime(2019, 12, 24, 14), True),
    (datetime.datetime(2018, 12, 25, 14), False),
    (datetime.datetime(2018, 12, 24, 23, 59), True),
])
def test_daytimematcher(dt, res):
    m = DayTimeMatcher(12, 24, 14, multiply=Decimal('1.25'))
    assert m(dt, dt, None) == res
