from datetime import datetime
from django.utils.formats import date_format


def test_now_01(assert_render):
    expected = "%d %d %d" % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )

    assert_render(template='{% now "j n Y" %}', context={}, expected=expected)


def test_now_02(assert_render):
    assert_render(
        template='{% now "DATE_FORMAT" %}',
        context={},
        expected=date_format(datetime.now()),
    )


def test_now_03(assert_render):
    expected = "%d %d %d" % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )
    assert_render(template="{% now 'j n Y' %}", context={}, expected=expected)


def test_now_04(assert_render):
    assert_render(
        template="{% now 'DATE_FORMAT' %}",
        context={},
        expected=date_format(datetime.now()),
    )


def test_now_05(assert_render):
    expected = '%d "%d" %d' % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )
    assert_render(template="{% now 'j \"n\" Y'%}", context={}, expected=expected)


def test_now_06(assert_render):
    expected = "%d '%d' %d" % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )
    assert_render(template="{% now \"j 'n' Y\"%}", context={}, expected=expected)


def test_now_07(assert_render):
    expected = "-%d %d %d-" % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )
    assert_render(
        template='{% now "j n Y" as N %}-{{N}}-', context={}, expected=expected
    )


def test_now_no_args(assert_parse_error):
    template = "{% now %}"
    django_message = "'now' statement takes one argument"
    rusty_message = """\
  × 'now' statement takes one argument
   ╭────
 1 │ {% now %}
   ·       ▲
   ·       ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_now_too_many_args(assert_parse_error):
    template = '{% now "j n Y" extra %}'
    rusty_message = """\
  × 'now' statement takes one argument
   ╭────
 1 │ {% now "j n Y" extra %}
   ·                ──┬──
   ·                  ╰── here
   ╰────
"""
    assert_parse_error(
        template=template,
        rusty_message=rusty_message,
        django_message="'now' statement takes one argument",
    )


def test_now_as_var_scope(assert_render):
    template = "{% now 'j n Y' as x %}{{ x }}|{{ x }}"
    expected = "%d %d %d|%d %d %d" % (
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
        datetime.now().day,
        datetime.now().month,
        datetime.now().year,
    )
    assert_render(template=template, context={}, expected=expected)


def test_now_as_without_name(assert_parse_error):
    template = '{% now "j n Y" as %}'
    assert_parse_error(
        template=template,
        django_message="'now' statement takes one argument",
        rusty_message="""\
  × 'now' statement takes one argument
   ╭────
 1 │ {% now "j n Y" as %}
   ·                ─┬
   ·                 ╰── here
   ╰────
""",
    )


def test_now_as_extra_tokens(assert_parse_error):
    template = '{% now "j n Y" as x y %}'
    assert_parse_error(
        template=template,
        django_message="'now' statement takes one argument",
        rusty_message="""\
  × 'now' statement takes one argument
   ╭────
 1 │ {% now "j n Y" as x y %}
   ·                     ┬
   ·                     ╰── here
   ╰────
""",
    )
