"""
Adapted Some tests from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_date.py
"""

from datetime import datetime, time

import pytest
from django.utils import timezone, translation


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            '{{ d|date:"m" }}',
            {"d": datetime(2008, 1, 1)},
            "01",
            id="test_date_01_month",
        ),
        pytest.param(
            "{{ d|date }}",
            {"d": datetime(2008, 1, 1)},
            "Jan. 1, 2008",
            id="test_date_02_default_format",
        ),
        pytest.param(
            "{{ d|date }}",
            {"d": "fail_string"},
            "",
            id="test_date_03_non_date",
        ),
        pytest.param(
            '{{ d|date:"o" }}',
            {"d": datetime(2008, 12, 29)},
            "2009",
            id="test_date_04_iso_year",
        ),
        pytest.param(
            '{{ d|date:"o" }}',
            {"d": datetime(2010, 1, 3)},
            "2009",
            id="test_date_05_iso_year_edge",
        ),
        pytest.param(
            '{{ d|date:"e" }}',
            {"d": datetime(2009, 3, 12, tzinfo=timezone.get_fixed_timezone(30))},
            "+0030",
            id="test_date_06_timezone_name",
        ),
        pytest.param(
            '{{ d|date:"e" }}',
            {"d": datetime(2009, 3, 12)},
            "",
            id="test_date_07_naive_datetime_timezone",
        ),
        pytest.param(
            '{{ t|date:"H:i" }}',
            {"t": time(0, 1)},
            "00:01",
            id="test_date_08_midnight_time",
        ),
        pytest.param(
            '{{ t|date:"H:i" }}',
            {"t": time(0, 0)},
            "00:00",
            id="test_date_09_exact_midnight",
        ),
    ],
)
def test_date(assert_render, template, context, expected):
    assert_render(template, context, expected)


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ var|date:'Y' }}",
            {"var": None},
            "",
            id="test_date_none",
        ),
        pytest.param(
            "{{ missing|date:'Y' }}",
            {},
            "",
            id="test_date_missing",
        ),
    ],
)
def test_date_empty_inputs(assert_render, template, context, expected):
    assert_render(template, context, expected)


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            '{{ d|date:"d F Y" }}',
            {"d": datetime(2005, 12, 29)},
            "29 December 2005",
            id="long_format",
        ),
        pytest.param(
            r'{{ d|date:"jS \o\f F" }}',
            {"d": datetime(2005, 12, 29)},
            "29th of December",
            id="escaped_characters",
        ),
        pytest.param('{{ d|date:"d F Y" }}', {"d": ""}, "", id="empty_string_input"),
        pytest.param('{{ d|date:"d F Y" }}', {"d": None}, "", id="none_input"),
    ],
)
def test_date_functional_scenarios(assert_render, template, context, expected):
    assert_render(template, context, expected)


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param("{{ d|date:'Y' }}", {"d": 123}, "", id="test_date_int_input"),
        pytest.param(
            "{{ d|date:'Y' }}", {"d": [2024, 1, 1]}, "", id="test_date_list_input"
        ),
        pytest.param(
            "{{ t|date:'Y' }}", {"t": time(12, 0)}, "", id="test_time_obj_with_year_fmt"
        ),
        pytest.param(
            "{{ t|date:'H' }}",
            {"t": time(13, 30)},
            "13",
            id="test_time_obj_with_hour_fmt",
        ),
    ],
)
def test_date_edges(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_date_localized(assert_render):
    template = "{{ d|date }}"
    with translation.override("fr"):
        assert_render(
            template=template,
            context={"d": datetime(2008, 1, 1)},
            expected="1 janvier 2008",
        )


def test_date_lazy_format(assert_render):
    template = '{{ t|date:_("H:i") }}'
    assert_render(
        template=template,
        context={"t": time(0, 0)},
        expected="00:00",
    )


def test_date_function():
    from django.template.defaultfilters import date

    assert date(datetime(2005, 12, 29), "d F Y") == "29 December 2005"
    assert date("") == ""
    assert date(None) == ""
    assert date(datetime(2005, 12, 29), r"jS \o\f F") == "29th of December"


def test_date_unexpected_argument(assert_parse_error):
    template = '{{ value|date:"Y":"m" }}'
    django_message = (
        'Could not parse the remainder: \':"m"\' from \'value|date:"Y":"m"\''
    )
    rusty_message = """\
  × Expected a valid filter name
   ╭────
 1 │ {{ value|date:"Y":"m" }}
   ·                   ─┬─
   ·                    ╰── here
   ╰────
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_date_error_propagation(assert_render_error):
    from datetime import date

    class ExplodingDate(date):
        @property
        def year(self):
            raise RuntimeError("Python execution failed")

    assert_render_error(
        template='{{ d|date:"Y" }}',
        context={"d": ExplodingDate(2024, 1, 1)},
        exception=RuntimeError,
        django_message="Python execution failed",
        rusty_message="Python execution failed",
    )
