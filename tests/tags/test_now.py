import pytest
import time_machine
from datetime import datetime
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.dateformat import format as django_format
from django.test import override_settings

# Year: 2026, Month: 1 (Jan), Day: 8, Hour: 12
FIXED_TIME = datetime(2026, 1, 8, 12, 0, 0)


@time_machine.travel(FIXED_TIME)
def test_now_basic_format(assert_render):
    expected = f"{FIXED_TIME.day} {FIXED_TIME.month} {FIXED_TIME.year}"
    assert_render(template='{% now "j n Y" %}', context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_named_setting(assert_render):
    assert_render(
        template='{% now "DATE_FORMAT" %}',
        context={},
        expected=date_format(FIXED_TIME),
    )


@time_machine.travel(FIXED_TIME)
def test_now_single_quotes(assert_render):
    expected = f"{FIXED_TIME.day} {FIXED_TIME.month} {FIXED_TIME.year}"
    assert_render(template="{% now 'j n Y' %}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_named_setting_single_quotes(assert_render):
    assert_render(
        template="{% now 'DATE_FORMAT' %}",
        context={},
        expected=date_format(FIXED_TIME),
    )


@time_machine.travel(FIXED_TIME)
def test_now_nested_double_quotes(assert_render):
    expected = f'{FIXED_TIME.day} "{FIXED_TIME.month}" {FIXED_TIME.year}'
    assert_render(template="{% now 'j \"n\" Y'%}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_nested_single_quotes(assert_render):
    expected = f"{FIXED_TIME.day} '{FIXED_TIME.month}' {FIXED_TIME.year}"
    assert_render(template="{% now \"j 'n' Y\"%}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_as_variable(assert_render):
    date_part = f"{FIXED_TIME.day} {FIXED_TIME.month} {FIXED_TIME.year}"
    expected = f"-{date_part}-"
    assert_render(
        template='{% now "j n Y" as N %}-{{N}}-', context={}, expected=expected
    )


def test_now_no_args(assert_parse_error):
    template = "{% now %}"
    django_message = "'now' statement takes one argument"
    rusty_message = """\
  × Expected a format string
   ╭────
 1 │ {% now %}
   ·       ▲
   ·       ╰── missing format
   ╰────
  help: The 'now' tag requires a format string, like "Y-m-d" or "DATE_FORMAT".
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_now_too_many_args(assert_parse_error):
    template = '{% now "j n Y" extra %}'
    rusty_message = """\
  × Unexpected argument after format string
   ╭────
 1 │ {% now "j n Y" extra %}
   ·                ──┬──
   ·                  ╰── unexpected argument
   ╰────
  help: If you want to store the result in a variable, use the 'as' keyword.
"""
    assert_parse_error(
        template=template,
        rusty_message=rusty_message,
        django_message="'now' statement takes one argument",
    )


@time_machine.travel(FIXED_TIME)
def test_now_as_var_scope(assert_render):
    template = "{% now 'j n Y' as x %}{{ x }}|{{ x }}"
    val = f"{FIXED_TIME.day} {FIXED_TIME.month} {FIXED_TIME.year}"
    expected = f"{val}|{val}"
    assert_render(template=template, context={}, expected=expected)


def test_now_as_without_name(assert_parse_error):
    template = '{% now "j n Y" as %}'
    assert_parse_error(
        template=template,
        django_message="'now' statement takes one argument",
        rusty_message="""\
  × Expected a variable name after 'as'
   ╭────
 1 │ {% now "j n Y" as %}
   ·                  ▲
   ·                  ╰── expected a variable name here
   ╰────
  help: Provide a name to store the date string, e.g. 'as my_var'
""",
    )


def test_now_as_extra_tokens(assert_parse_error):
    template = '{% now "j n Y" as x y %}'
    assert_parse_error(
        template=template,
        django_message="'now' statement takes one argument",
        rusty_message="""\
  × Unexpected argument after variable name
   ╭────
 1 │ {% now "j n Y" as x y %}
   ·                     ┬
   ·                     ╰── extra argument
   ╰────
  help: The 'now' tag only accepts one variable assignment. Try removing this
        extra argument.
""",
    )


@time_machine.travel(FIXED_TIME)
def test_now_named_formats(assert_render):
    formats = ["TIME_FORMAT", "SHORT_DATE_FORMAT", "YEAR_MONTH_FORMAT"]
    for fmt in formats:
        assert_render(
            template=f'{{% now "{fmt}" %}}',
            context={},
            expected=date_format(FIXED_TIME, fmt),
        )


@time_machine.travel(FIXED_TIME)
def test_now_empty_string(assert_render):
    expected = date_format(FIXED_TIME)
    assert_render(template='{% now "" %}', context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_as_var_overwrite(assert_render):
    expected = FIXED_TIME.strftime("%Y")
    template = "{% now 'Y' as x %}{{ x }}"
    assert_render(template=template, context={"x": "old"}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_as_var_overwrites_none(assert_render):
    expected = FIXED_TIME.strftime("%Y")
    assert_render(
        template="{% now 'Y' as x %}{{ x }}", context={"x": None}, expected=expected
    )


@time_machine.travel(FIXED_TIME)
def test_now_unicode_and_escapes(assert_render):
    expected = f"{FIXED_TIME.day} o {FIXED_TIME.month}"
    assert_render(template=r"{% now 'j \o n' %}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_non_ascii_format(assert_render):
    expected = f"{FIXED_TIME.year} • {FIXED_TIME.month}"
    assert_render(template="{% now 'Y • n' %}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_very_long_format(assert_render):
    long_format = " ".join(["Y"] * 1000)
    year = FIXED_TIME.strftime("%Y")
    expected = " ".join([year] * 1000)
    assert_render(
        template=f'{{% now "{long_format.strip()}" %}}',
        context={},
        expected=expected.strip(),
    )


@override_settings(USE_TZ=True, TIME_ZONE="UTC")
@time_machine.travel(FIXED_TIME)
def test_now_timezone_aware(assert_render):
    now = timezone.now()
    expected = django_format(now, "H")
    assert_render(template="{% now 'H' %}", context={}, expected=expected)


@override_settings(USE_TZ=False)
@time_machine.travel(FIXED_TIME)
def test_now_timezone_naive(assert_render):
    expected = FIXED_TIME.strftime("%H")
    assert_render(template="{% now 'H' %}", context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_single_quote_incomplete(assert_render):
    assert_render(
        template="{% now ' %}",
        context={},
        expected=date_format(FIXED_TIME, "DATE_FORMAT"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_double_quote_incomplete(assert_render):
    assert_render(
        template='{% now " %}',
        context={},
        expected=date_format(FIXED_TIME, "DATE_FORMAT"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_numeric_format(assert_render):
    assert_render(
        template="{% now 123 %}",
        context={},
        expected=django_format(FIXED_TIME, "2"),
    )


@pytest.mark.parametrize(
    "fmt",
    [
        "TIME_FORMAT",
        "DATE_FORMAT",
        "DATETIME_FORMAT",
        "SHORT_DATE_FORMAT",
        "SHORT_DATETIME_FORMAT",
    ],
)
@time_machine.travel(FIXED_TIME)
def test_now_all_named_logic(assert_render, fmt):
    assert_render(
        template=f'{{% now "{fmt}" %}}',
        context={},
        expected=date_format(FIXED_TIME, fmt),
    )


@time_machine.travel(FIXED_TIME)
def test_now_as_different_name(assert_render):
    assert_render(
        template='{% now "Y" as current_year %}Year: {{ current_year }}',
        context={},
        expected=f"Year: {FIXED_TIME.year}",
    )


@time_machine.travel(FIXED_TIME)
def test_now_empty_format(assert_render):
    assert_render(
        template='{% now "" %}',
        context={},
        expected=date_format(FIXED_TIME, "DATE_FORMAT"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_escaped_same_quote(assert_render):
    expected = f'{FIXED_TIME.day} " {FIXED_TIME.month}'
    assert_render(
        template=r"{% now 'j \" n' %}",
        context={},
        expected=expected,
    )


@time_machine.travel(FIXED_TIME)
def test_now_excessive_whitespace(assert_render):
    expected = FIXED_TIME.strftime("%Y")
    assert_render(
        template='{%   now    "Y"      %}',
        context={},
        expected=expected,
    )


@time_machine.travel(FIXED_TIME)
def test_now_tabs(assert_render):
    expected = FIXED_TIME.strftime("%Y")
    assert_render(
        template='{%\tnow\t"Y"\t%}',
        context={},
        expected=expected,
    )


def test_now_as_uppercase(assert_parse_error):
    assert_parse_error(
        template='{% now "Y" AS x %}',
        django_message="'now' statement takes one argument",
        rusty_message="""\
  × Unexpected argument after format string
   ╭────
 1 │ {% now "Y" AS x %}
   ·            ─┬
   ·             ╰── unexpected argument
   ╰────
  help: If you want to store the result in a variable, use the 'as' keyword.
""",
    )


@time_machine.travel(FIXED_TIME)
def test_now_format_named_as(assert_render):
    assert_render(
        template='{% now "as" %}',
        context={},
        expected=django_format(FIXED_TIME, "as"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_as_var_named_now(assert_render):
    assert_render(
        template='{% now "Y" as now %}{{ now }}',
        context={},
        expected=str(FIXED_TIME.year),
    )


@time_machine.travel(FIXED_TIME)
def test_now_overwrites_nested_context(assert_render):
    context = {"x": {"y": "old"}}
    assert_render(
        template='{% now "Y" as x %}{{ x }}',
        context=context,
        expected=str(FIXED_TIME.year),
    )


@time_machine.travel(FIXED_TIME)
def test_now_reassign_same_var(assert_render):
    assert_render(
        template='{% now "Y" as x %}{% now "n" as x %}{{ x }}',
        context={},
        expected=str(FIXED_TIME.month),
    )


@time_machine.travel(FIXED_TIME)
def test_now_invalid_format_tokens(assert_render):
    assert_render(
        template='{% now "Q W Z" %}',
        context={},
        expected=django_format(FIXED_TIME, "Q W Z"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_literal_percent(assert_render):
    assert_render(
        template="{% now 'Y %% m' %}",
        context={},
        expected=django_format(FIXED_TIME, "Y %% m"),
    )


@time_machine.travel(FIXED_TIME)
def test_now_long_variable_name(assert_render):
    var = "x" * 10_000
    assert_render(
        template=f'{{% now "Y" as {var} %}}{{{{ {var} }}}}',
        context={},
        expected=str(FIXED_TIME.year),
    )


@time_machine.travel(FIXED_TIME)
def test_now_many_invocations(assert_render):
    template = " ".join(['{% now "Y" %}'] * 1000)
    expected = " ".join([str(FIXED_TIME.year)] * 1000)
    assert_render(template=template, context={}, expected=expected)


@time_machine.travel(FIXED_TIME)
def test_now_garbage_format(assert_render):
    assert_render(
        template="{% now '%%%INVALID%%%' %}",
        context={},
        expected="%%%0Jan.VPMFalse0Thu%%%",
    )


@time_machine.travel(FIXED_TIME)
def test_now_unknown_named_format_literal(assert_render):
    assert_render(
        template="{% now 'NOT_A_REAL_FORMAT' %}",
        context={},
        expected="Jan.+0000UTC_PM_RJanuaryPMFalse_January+0000RJanPMUTC",
    )


@time_machine.travel(FIXED_TIME)
def test_now_weird_mixed_quotes(assert_render):
    assert_render(
        template="""{% now "'Y'" %}""",
        context={},
        expected=f"'{str(FIXED_TIME.year)}'",
    )


@time_machine.travel(FIXED_TIME)
def test_now_format_from_context(assert_render):
    assert_render(
        template="{% now format_var %}",
        context={"format_var": "j n Y"},
        expected="2026Thu, 08 Jan 2026 12:00:00 +000001p.m.31_vp.m.",
    )


@time_machine.travel(FIXED_TIME)
def test_now_invalid_remainder(assert_render):
    template = '{% now "Y"invalid %}'
    assert_render(
        template=template,
        context={},
        expected=r'2026"001vp.m.Thursday00',
    )
