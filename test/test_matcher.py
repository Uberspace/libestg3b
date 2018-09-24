import datetime
from decimal import Decimal

import pytest

from libestg3b.rule import DayRule, DayTimeRule, Rule, RuleGroup


@pytest.fixture
def make_rule_group():
    def m(**kwargs):
        return RuleGroup(**{
            "slug": "SR_GRP",
            "description": "Some Rule Group",
            "rules": [],
            **kwargs,
        })

    return m


@pytest.fixture
def rule_group(make_rule_group):
    return make_rule_group()


def test_rule_init():
    m = Rule('A', 'a', lambda x: False, add=Decimal('1'))
    m.match(None, None, None)


def test_rule_init_decimal_multiply():
    with pytest.raises(AssertionError):
        Rule('A', 'a', lambda x: False, multiply=0.1)


def test_rule_init_decimal_add():
    with pytest.raises(AssertionError):
        Rule('A', 'a', lambda x: False, add=0.1)


def test_rule_init__no_add_or_multiply():
    with pytest.raises(AssertionError):
        Rule('A', 'a', lambda x: False)


def test_rule_init_add_and_multiply():
    with pytest.raises(AssertionError):
        Rule('A', 'a', lambda x: False, add=Decimal('1'), multiply=Decimal('2'))


def test_rule_init_no_slug():
    with pytest.raises(AssertionError):
        Rule('', 'xx', lambda x: False)


def test_rule_init_no_description():
    with pytest.raises(AssertionError):
        Rule('X', '', lambda x: False)


@pytest.mark.parametrize("impl", [
    lambda: False,
    lambda a, b, c, d: False,
])
def test_rule_init_impl_nargs_crash(impl):
    with pytest.raises(AssertionError):
        Rule('A', 'a', impl)


@pytest.mark.parametrize("impl", [
    lambda a: False,
    lambda a: True,
])
def test_rule_call_rtn_type(impl):
    m = Rule('A', 'a', impl, add=Decimal('1'))
    m.match(None, None, None)


def test_rule_call_rtn_type_crash():
    m = Rule('A', 'a', lambda x: None, add=Decimal('1'))
    with pytest.raises(AssertionError):
        m.match(None, None, None)


def test_rule_call_passing_1():
    args = None

    def impl(a):
        nonlocal args
        args = [a]
        return True

    m = Rule('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0]


def test_rule_call_passing_2():
    args = None

    def impl(a, b):
        nonlocal args
        args = [a, b]
        return True

    m = Rule('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0, 1]


def test_rule_call_passing_3():
    args = None

    def impl(a, b, c):
        nonlocal args
        args = [a, b, c]
        return True

    m = Rule('A', 'a', impl, add=Decimal('1'))
    m.match(0, 1, 2)
    assert args == [0, 1, 2]


def test_macher_eq():
    m1 = Rule('A', 'a', lambda f: True, add=Decimal('1'))
    m2 = Rule('A', 'a', lambda f: True, add=Decimal('2'))
    assert m1 == m2


def test_macher_str():
    m = Rule('SLUG', 'description', lambda f: True, add=Decimal('1'))
    assert 'SLUG' in str(m)
    assert 'description' in str(m)


def test_macher_ltgt_add():
    m1 = Rule('A', 'a', lambda f: True, add=Decimal('1'))
    m2 = Rule('A', 'a', lambda f: True, add=Decimal('2'))
    assert m1 < m2
    assert not(m2 < m1)
    assert m2 > m1
    assert not(m1 > m2)


def test_macher_ltgt_multiply():
    m1 = Rule('A', 'a', lambda f: True, multiply=Decimal('1'))
    m2 = Rule('A', 'a', lambda f: True, multiply=Decimal('2'))
    assert m1 < m2
    assert not(m2 < m1)
    assert m2 > m1
    assert not(m1 > m2)


def test_macher_ltgt_incompatible():
    m1 = Rule('A', 'a', lambda f: True, add=Decimal('1'))
    m2 = Rule('A', 'a', lambda f: True, multiply=Decimal('2'))

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
def test_DayRule(dt, res):
    m = DayRule('XXX', 12, 26, multiply=Decimal('1.25'))
    assert m.match(dt, dt, None) == res


@pytest.mark.parametrize('dt,res', [
    (datetime.datetime(2018, 12, 24, 0), False),
    (datetime.datetime(2018, 12, 24, 13, 59), False),
    (datetime.datetime(2018, 12, 24, 14), True),
    (datetime.datetime(2019, 12, 24, 14), True),
    (datetime.datetime(2018, 12, 25, 14), False),
    (datetime.datetime(2018, 12, 24, 23, 59), True),
])
def test_daytimeRule(dt, res):
    m = DayTimeRule('XXX', 12, 24, 14, multiply=Decimal('1.25'))
    assert m.match(dt, dt, None) == res


def test_rulegroup():
    RuleGroup('XXX', 'xxx', [])


def test_rulegroup_init():
    mg = RuleGroup('XXX', 'xxx', [DayRule('mmm', 1, 1, multiply=Decimal('2'))])
    assert mg._description == 'xxx'
    assert len(mg._rules) == 1
    assert mg._rules['mmm']._slug == 'mmm'


def test_rulegroup_duplicate():
    with pytest.raises(Exception):
        RuleGroup('XXX', 'xxx', [
            DayRule('mmm', 1, 1, multiply=Decimal('2')),
            DayRule('mmm', 1, 1, multiply=Decimal('2')),
        ])


def test_rulegroup_append(rule_group):
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    assert len(rule_group._rules) == 1
    assert rule_group._rules['mmm']._slug == 'mmm'


def test_rulegroup_append_duplicate(rule_group):
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    with pytest.raises(Exception):
        rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    assert len(rule_group._rules) == 1
    assert rule_group._rules['mmm']._slug == 'mmm'


def test_rulegroup_append_replace(rule_group):
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('3')), replace=True)
    assert len(rule_group._rules) == 1
    assert rule_group._rules['mmm']._slug == 'mmm'
    assert rule_group._rules['mmm']._multiply == Decimal("3")


def test_rulegroup_append_non_Rule(rule_group):
    with pytest.raises(Exception):
        rule_group.append("bla")


def test_rulegroup_append_wrong_type(rule_group):
    rule_group.append(DayRule('mmm1', 1, 1, multiply=Decimal('2')))
    with pytest.raises(Exception):
        rule_group.append(DayRule('mmm2', 2, 2, add=Decimal('2')))


def test_rulegroup_extend(rule_group):
    rule_group.extend([
        DayRule('mmm1', 1, 1, multiply=Decimal('2')),
        DayRule('mmm2', 1, 2, multiply=Decimal('2')),
        DayRule('mmm3', 1, 3, multiply=Decimal('2')),
    ])
    assert len(rule_group._rules) == 3
    assert rule_group._rules['mmm1']._slug == 'mmm1'
    assert rule_group._rules['mmm2']._slug == 'mmm2'
    assert rule_group._rules['mmm3']._slug == 'mmm3'


def test_rulegroup_extend_duplicate(rule_group):
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    with pytest.raises(Exception):
        rule_group.extend([DayRule('mmm', 1, 1, multiply=Decimal('3'))])
    assert len(rule_group._rules) == 1
    assert rule_group._rules['mmm']._multiply == Decimal("2")


def test_rulegroup_extend_replace(rule_group):
    rule_group.append(DayRule('mmm', 1, 1, multiply=Decimal('2')))
    rule_group.extend([DayRule('mmm', 1, 1, multiply=Decimal('3'))], replace=True)
    assert len(rule_group._rules) == 1
    assert rule_group._rules['mmm']._multiply == Decimal("3")


def test_rulegroup_contains(make_rule_group):
    mg = make_rule_group(rules=[DayRule('mmm', 1, 1, multiply=Decimal('2'))])
    assert 'mmm' in mg
    assert DayRule('mmm', 1, 1, multiply=Decimal('2')) in mg


def test_rulegroup_iter(make_rule_group):
    mg = make_rule_group(rules=[
        DayRule('mmm1', 1, 1, multiply=Decimal('2')),
        DayRule('mmm2', 2, 2, multiply=Decimal('2')),
    ])

    i = iter(mg)

    assert next(i)._slug == 'mmm1'
    assert next(i)._slug == 'mmm2'

    with pytest.raises(StopIteration):
        next(i)
