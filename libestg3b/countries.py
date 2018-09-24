from decimal import Decimal

from libestg3b.estg3b import EStG3bBase
from libestg3b.rule import DayRule, DayTimeRule, Rule, RuleGroup

R = Rule


class EStG3bGermany(EStG3bBase):
    aliases = [
        'GERMANY',
        'DE',
    ]

    def __init__(self, **kwargs):
        rules = (
            RuleGroup('GRP_DE_NIGHT', 'Nachtarbeit', (
                R(
                    'DE_NIGHT', 'Nachtarbeit 20:00-06:00',
                    lambda m: m.hour >= 20 or m.hour < 6, multiply=Decimal('0.25'),
                    tests=(
                        ('~19:59', False),
                        ('~20:00', True),
                        ('~21:00', True),
                        ('~05:59', True),
                        ('~06:00', False),
                    ),
                ),
                R(
                    'DE_NIGHT_START_YESTERDAY', 'Nachtarbeit 00:00-04:00 (Folgetag)',
                    lambda m, s: 0 <= m.hour < 4 and s.date() < m.date(), multiply=Decimal('0.4'),
                    tests=(
                        ('00:00~00:01', False),
                        ('23:59~00:01', True),
                        ('23:59~03:59', True),
                        ('23:59~04:00', False),
                    )
                ),
            )),
            RuleGroup('GRP_HOLIDAYS', 'Sonntags und Feiertagsarbeit', (
                R(
                    'DE_SUNDAY', 'Sonntagsarbeit',
                    lambda m: m.weekday() == 6, multiply=Decimal('0.5'),
                    tests=(
                        ('~2018-09-15', False),
                        ('~2018-09-16 00:00', True),
                        ('~2018-09-16 23:59', True),
                        ('2018-09-16 23:59~2018-09-17 00:00', False),
                    ),
                ),
                R(
                    'DE_SUNDAY_NEXT_NIGHT', 'Sonntagsarbeit (Montag)',
                    lambda m, s: s.weekday() == 6 and 0 <= m.hour < 4, multiply=Decimal('0.5'),
                    tests=(
                        # 2018-09-16 is a Sunday
                        ('~2018-09-16 00:00', False),
                        ('~2018-09-16 23:59', False),
                        ('2018-09-16 23:59~2018-09-17 00:00', True),
                        ('2018-09-16 23:59~2018-09-17 03:59', True),
                        ('2018-09-16 23:59~2018-09-17 04:00', False),
                        ('2018-09-17 23:59~2018-09-18 00:00', False),
                    ),
                ),
                R(
                    'DE_HOLIDAY', 'Feiertagsarbeit',
                    lambda m, s, holidays: m in holidays, multiply=Decimal('1.25'),
                    tests=(
                        # 2018-05-10 is Christi Himmelfahrt
                        ('~2018-05-09 23:59', False),
                        ('~2018-05-10 00:00', True),
                        ('~2018-05-10 23:59', True),
                        ('~2018-05-11 00:00', False),
                        ('2018-05-10 23:59~2018-05-11 00:00', False),
                    ),
                ),
                R(
                    'DE_HOLIDAY_NEXT_NIGHT', 'Feiertagsarbeit (Folgetag)',
                    lambda m, s, holidays: s in holidays and 0 <= m.hour < 4, multiply=Decimal('1.25'),
                    tests=(
                        # 2018-05-10 is Christi Himmelfahrt
                        ('~2018-05-10 00:00', False),
                        ('~2018-05-10 23:59', False),
                        ('2018-05-10 23:59~2018-05-11 00:00', True),
                        ('2018-05-10 23:59~2018-05-11 03:59', True),
                        ('2018-05-10 23:59~2018-05-11 04:00', False),
                        ('2018-09-11 23:59~2018-05-12 00:00', False),
                    )
                ),
                DayTimeRule('DE_HEILIGABEND', 12, 24, 14, multiply=Decimal('1.25')),
                DayTimeRule('DE_SILVESTER', 12, 31, 14, multiply=Decimal('1.25')),
                DayRule('DE_WEIHNACHTSFEIERTAG_1', 12, 25, multiply=Decimal('1.5')),
                DayRule('DE_WEIHNACHTSFEIERTAG_2', 12, 26, multiply=Decimal('1.5')),
                DayRule('DE_TAGDERARBEIT', 5, 1, multiply=Decimal('1.5')),
            )),
        )
        super().__init__('DE', rules, **kwargs)
