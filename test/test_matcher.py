import datetime
from decimal import Decimal

import pytest

from libestg3b.matcher import DayMatcher, DayTimeMatcher, Matcher, MatcherGroup


def test_matcher_init():
    m = Matcher('A', 'a', lambda x: False, add=Decimal('1'))
    m.match(None, None, None)


def test_matcher_init_decimal_multiply():
    with pytest.raises(AssertionError):
        Matcher('A', 'a', lambda x: False, multiply=0.1)


def test_matcher_init_decimal_add():
    with pytest.raises(AssertionError):
        Matcher('A', 'a', lambda x: False, add=0.1)


def test_matcher_init__no_add_or_multiply():
    with pytest.raises(AssertionError):
        Matcher('A', 'a', lambda x: False)


def test_matcher_init_add_and_multiply():
    with pytest.raises(AssertionError):
        Matcher('A', 'a', lambda x: False, add=Decimal('1'), multiply=Decimal('2'))


def test_matcher_init_no_slug():
    with pytest.raises(AssertionError):
        Matcher('', 'xx', lambda x: False)


def test_matcher_init_no_description():
    with pytest.raises(AssertionError):
        Matcher('X', '', lambda x: False)


@pytest.mark.parametrize("impl", [
    lambda: False,
    lambda a, b, c, d: False,
])
def test_matcher_init_impl_nargs_crash(impl):
    with pytest.raises(AssertionError):
        Matcher('A', 'a', impl)


@pytest.mark.parametrize("impl", [
    lambda a: False,
    lambda a: True,
])
def test_matcher_call_rtn_type(impl):
    m = Matcher('A', 'a', impl, add=Decimal('1'))
    m.match(None, None, None)


def test_matcher_call_rtn_type_crash():
    m = Matcher('A', 'a', lambda x: None, add=Decimal('1'))
    with pytest.raises(AssertionError):
        m.match(None, None, None)


def test_matcher_call_passing_1():
    args = None

    def impl(a):
        nonlocal args
        args = [a]
        return True

    m = Matcher('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0]


def test_matcher_call_passing_2():
    args = None

    def impl(a, b):
        nonlocal args
        args = [a, b]
        return True

    m = Matcher('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0, 1]


def test_matcher_call_passing_3():
    args = None

    def impl(a, b, c):
        nonlocal args
        args = [a, b, c]
        return True

    m = Matcher('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0, 1, 2]


def test_macher_ltgt_add():
    m1 = Matcher('A', 'a', lambda f: True, add=Decimal('1'))
    m2 = Matcher('A', 'a', lambda f: True, add=Decimal('2'))
    assert m1 < m2
    assert not(m2 < m1)
    assert m2 > m1
    assert not(m1 > m2)


def test_macher_ltgt_multiply():
    m1 = Matcher('A', 'a', lambda f: True, multiply=Decimal('1'))
    m2 = Matcher('A', 'a', lambda f: True, multiply=Decimal('2'))
    assert m1 < m2
    assert not(m2 < m1)
    assert m2 > m1
    assert not(m1 > m2)


def test_macher_ltgt_incompatible():
    m1 = Matcher('A', 'a', lambda f: True, add=Decimal('1'))
    m2 = Matcher('A', 'a', lambda f: True, multiply=Decimal('2'))

    with pytest.raises(Exception):
        m1 < m2
    with pytest.raises(Exception):
        m1 > m2


@pytest.mark.parametrize('dt,res', [
    (datetime.datetime(2018, 12, 25, 23, 59), False),
    (datetime.datetime(2018, 12, 26, 0), True),
    (datetime.datetime(2018, 12, 26, 23, 59), True),
    (datetime.datetime(2018, 12, 27, 0), False),
    (datetime.datetime(2019, 12, 26, 0), True),
])
def test_daymatcher(dt, res):
    m = DayMatcher('XXX', 12, 26, multiply=Decimal('1.25'))
    assert m.match(dt, dt, None) == res


@pytest.mark.parametrize('dt,res', [
    (datetime.datetime(2018, 12, 24, 0), False),
    (datetime.datetime(2018, 12, 24, 13, 59), False),
    (datetime.datetime(2018, 12, 24, 14), True),
    (datetime.datetime(2019, 12, 24, 14), True),
    (datetime.datetime(2018, 12, 25, 14), False),
    (datetime.datetime(2018, 12, 24, 23, 59), True),
])
def test_daytimematcher(dt, res):
    m = DayTimeMatcher('XXX', 12, 24, 14, multiply=Decimal('1.25'))
    assert m.match(dt, dt, None) == res


def test_matchergroup():
    MatcherGroup('xxx', [])


def test_matchergroup_init():
    mg = MatcherGroup('xxx', [DayMatcher('mmm', 1, 1, multiply=Decimal('2'))])
    assert mg._description == 'xxx'
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._slug == 'mmm'


def test_matchergroup_duplicate():
    with pytest.raises(Exception):
        MatcherGroup('xxx', [
            DayMatcher('mmm', 1, 1, multiply=Decimal('2')),
            DayMatcher('mmm', 1, 1, multiply=Decimal('2')),
        ])


def test_matchergroup_append():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._slug == 'mmm'


def test_matchergroup_append_duplicate():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    with pytest.raises(Exception):
        mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._slug == 'mmm'


def test_matchergroup_append_replace():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('3')), replace=True)
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._slug == 'mmm'
    assert mg._matchers['mmm']._multiply == Decimal("3")


def test_matchergroup_extend():
    mg = MatcherGroup('xxx', [])
    mg.extend([
        DayMatcher('mmm1', 1, 1, multiply=Decimal('2')),
        DayMatcher('mmm2', 1, 2, multiply=Decimal('2')),
        DayMatcher('mmm3', 1, 3, multiply=Decimal('2')),
    ])
    assert len(mg._matchers) == 3
    assert mg._matchers['mmm1']._slug == 'mmm1'
    assert mg._matchers['mmm2']._slug == 'mmm2'
    assert mg._matchers['mmm3']._slug == 'mmm3'


def test_matchergroup_extend_duplicate():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    with pytest.raises(Exception):
        mg.extend([DayMatcher('mmm', 1, 1, multiply=Decimal('3'))])
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._multiply == Decimal("2")


def test_matchergroup_extend_replace():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
    mg.extend([DayMatcher('mmm', 1, 1, multiply=Decimal('3'))], replace=True)
    assert len(mg._matchers) == 1
    assert mg._matchers['mmm']._multiply == Decimal("3")


def test_matchergroup_contains():
    mg = MatcherGroup('xxx', [DayMatcher('mmm', 1, 1, multiply=Decimal('2'))])
    assert 'mmm' in mg
    assert DayMatcher('mmm', 1, 1, multiply=Decimal('2')) in mg


def test_matchergroup_iter():
    mg = MatcherGroup('xxx', [
        DayMatcher('mmm1', 1, 1, multiply=Decimal('2')),
        DayMatcher('mmm2', 2, 2, multiply=Decimal('2')),
    ])

    i = iter(mg)

    assert next(i)._slug == 'mmm1'
    assert next(i)._slug == 'mmm2'

    with pytest.raises(StopIteration):
        next(i)


def test_matchergroup_append_non_matcher():
    mg = MatcherGroup('xxx', [])

    with pytest.raises(Exception):
        mg.append("bla")


def test_matchergroup_append_duplicate():
    mg = MatcherGroup('xxx', [])
    mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))

    with pytest.raises(Exception):
        mg.append(DayMatcher('mmm', 1, 1, multiply=Decimal('2')))
