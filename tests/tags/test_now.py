from datetime import datetime
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.dateformat import format as django_format
from django.test import override_settings


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
  × Expected an argument
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


def test_now_named_formats(assert_render):
    now = datetime.now()
    formats = ["TIME_FORMAT", "SHORT_DATE_FORMAT", "YEAR_MONTH_FORMAT"]
    for fmt in formats:
        assert_render(
            template=f'{{% now "{fmt}" %}}', context={}, expected=date_format(now, fmt)
        )


def test_now_empty_string(assert_render):
    expected = date_format(datetime.now())
    assert_render(template='{% now "" %}', context={}, expected=expected)


def test_now_as_var_overwrite(assert_render):
    expected = str(datetime.now().year)
    template = "{% now 'Y' as x %}{{ x }}"
    assert_render(template=template, context={"x": "old"}, expected=expected)


def test_now_as_var_overwrites_none(assert_render):
    expected = str(datetime.now().year)
    assert_render(
        template="{% now 'Y' as x %}{{ x }}", context={"x": None}, expected=expected
    )


def test_now_unicode_and_escapes(assert_render):
    now = datetime.now()
    expected = f"{now.day} o {now.month}"
    assert_render(template=r"{% now 'j \o n' %}", context={}, expected=expected)


def test_now_non_ascii_format(assert_render):
    now = datetime.now()
    expected = f"{now.year} • {now.month}"
    assert_render(template="{% now 'Y • n' %}", context={}, expected=expected)


def test_now_very_long_format(assert_render):
    long_format = "Y " * 1000
    year = str(datetime.now().year)
    expected = (year + " ") * 1000
    assert_render(
        template=f'{{% now "{long_format.strip()}" %}}',
        context={},
        expected=expected.strip(),
    )


@override_settings(USE_TZ=True, TIME_ZONE="UTC")
def test_now_timezone_aware(assert_render):
    now = timezone.now()
    expected = django_format(now, "H")
    assert_render(template="{% now 'H' %}", context={}, expected=expected)


@override_settings(USE_TZ=False)
def test_now_timezone_naive(assert_render):
    expected = str(datetime.now().hour)
    assert_render(template="{% now 'H' %}", context={}, expected=expected)
