using libestg3b
===============

1. have people work on weekends
2. have them write down when exactly
3. pipe information into libestg3b
4. have it tell you which shifts are relevant for extra pay, and how much
5. ???
6. PROFIT!


Prerequisites
-------------

To use this library, you need some kind of a system to track how many hours were
spent working. In some cases, this may be a simple CSV file, a web tool to track
work hours or an export from your fancy SAP application. In any case, you need a
list of hours worked, each with a start and end date and time.

In this example we will use the easiest source: a text file, ``work.txt``::

    2018-09-22T18:00:00 2018-09-22T20:00:00
    2018-09-23T02:00:00 2018-09-23T03:00:00
    2018-09-24T22:00:00 2018-09-25T01:00:00

So, we've got data. Now make it into a list of ``datetime`` objects:

.. code-block:: python

    import dateutil.parser

    def parse_work():
        with open('work.txt') as f:
          return (
              (dateutil.parser.parse(l[0]), dateutil.parser.parse(l[1]))
              for l in map(lambda l: l.split(' '), f.readlines())
          )

    def main():
        shifts = parse_work()

    if __name__ == '__main__':
        main()

Great! That's all we need to get libestg3b running.


Turning shifts into bonuses
---------------------------

The main functionality of libestg3b is to turn a shift into a list of matching
rules defined by law. For example, the German law mandates, that work on sundays
can be paid 50% more; work in the night receives a bonus of up to 40%, depending
on the exact times.

Let's use the shift data we've got and see what :meth:`~libestg3b.EStG3bBase.calculate_shifts`
can tell us about it:

.. code-block:: python

    ...

    shifts = libestg3b.EStG3b('DE')().calculate_shifts(shifts)

    # for each input shift, calculate_shifts returned one object ...
    for shift in shifts:
        # ... which is a list of rule matches
        for match in shift:
            print(match)

When we run the script with the new code added in the last example, we get::

    <Match 2018-09-22T18:00:00~2018-09-22T20:00:00, None, add=0, multiply=0>
    <Match 2018-09-23T02:00:00~2018-09-23T03:00:00, DE_NIGHT+DE_SUNDAY, add=0, multiply=0.75>
    <Match 2018-09-24T22:00:00~2018-09-25T00:00:00, DE_NIGHT, add=0, multiply=0.25>
    <Match 2018-09-25T00:00:00~2018-09-25T01:00:00, DE_NIGHT_START_YESTERDAY, add=0, multiply=0.4>

As you can see, our three shifts turned into four matches. Let's talk about what
happened here:

1. | `09-22 18:00` to `09-22 20:00`
   | Probably the most boring example there is. Not a single rule matched.
2. | `09-23 02:00` to `09-23 03:00`
   | A combination of two rules: ``DE_NIGHT`` (25%) and ``DE_SUNDAY`` (50%).
     Since the law allows combination in this case, we end up with a total bonus
     of 75%.
3. | `09-24 22:00` to `09-25T01:00`
   | This one is fun! Again, two matching rules were found, but each of them is
     not able to cover the whole shift. Therefore we get two :class:`~libestg3b.Match`
     objects: one for the first two hours (``DE_NIGHT``, 25%) and one just for
     the last hour (``DE_NIGHT_START_YESTERDAY``, 40%).

Note that ``multiply`` values are given as `0.xx`, not `1.xx` as is common. This
is to enable simply combination of multiple rules: ``1.2 + 1.2`` equals ``2.4``,
which is too high, but ``0.2 + 0.2`` equals the correct ``0.4``.

Making money out of matches
---------------------------

The :class:`~libestg3b.Match` object only tells us how to modify the base salary
people get. While this is useful information, accounting likes to get absolute
numbers. As you can see in the output above, rules can modify the salary in two
ways: add a fixed amount (5€ more), multiply by some factor (20% more). Since
our example is based on German law, which only works with percentages, we can
simplify our code.

To determine the amount of money to be payed out, have a look at the ``bonus_*``
and ``hours`` attributes. The first one tells us how much to increase the base
salary, the 2nd one tells us how much time was actually relevant.

.. code-block:: python

    import libestg3b

    def main():
        shifts = parse_work()
        shifts = libestg3b.EStG3b('DE')().calculate_shifts(shifts)
        base_salary = Decimal(25)
        total = Decimal(0)

        for shift in shifts:
            for match in shift:
                bonus = match.bonus_multiply + 1
                eur = base_salary * match.hours * bonus
                total = total + eur

                print(match)
                print(f'({base_salary}€ * {bonus:.2f}) * {match.hours}h = {eur: 2.2f}€')

        print(f'\nTotal: {total:.2f}€')

... and when we run it::

    <Match 2018-09-22T18:00:00~2018-09-22T20:00:00, None, add=0, multiply=0>
    (25€ * 1.00) * 2h =  50.00€
    <Match 2018-09-23T02:00:00~2018-09-23T03:00:00, DE_NIGHT+DE_SUNDAY, add=0, multiply=0.75>
    (25€ * 1.75) * 1h =  43.75€
    <Match 2018-09-24T22:00:00~2018-09-25T00:00:00, DE_NIGHT, add=0, multiply=0.25>
    (25€ * 1.25) * 2h =  62.50€
    <Match 2018-09-25T00:00:00~2018-09-25T01:00:00, DE_NIGHT_START_YESTERDAY, add=0, multiply=0.4>
    (25€ * 1.40) * 1h =  35.00€

    Total: 191.25€


That's it, bascially. Depending on your exact needs, you can now put this code
into a CSV, throw it at some API or just print it out.

Have fun!
