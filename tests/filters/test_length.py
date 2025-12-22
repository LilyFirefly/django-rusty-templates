"""
Adapted from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_length.py
"""

import pytest
from django.utils.safestring import mark_safe


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ list|length }}",
            {"list": ["4", None, True, {}]},
            "4",
            id="test_length_01",
        ),
        pytest.param(
            "{{ list|length }}",
            {"list": []},
            "0",
            id="test_length_02",
        ),
        pytest.param(
            "{{ string|length }}",
            {"string": ""},
            "0",
            id="test_length_03",
        ),
        pytest.param(
            "{{ string|length }}",
            {"string": "django"},
            "6",
            id="test_length_04",
        ),
        pytest.param(
            "{% if string|length == 6 %}Pass{% endif %}",
            {"string": mark_safe("django")},
            "Pass",
            id="test_length_05",
        ),
        pytest.param(
            "{{ int|length }}",
            {"int": 7},
            "0",
            id="test_length_06",
        ),
        pytest.param(
            "{{ None|length }}",
            {"None": None},
            "0",
            id="test_length_07",
        ),
    ],
)
def test_length(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_length_unicode_01(assert_render):
    template = "{{ var|lower|length }}"
    assert_render(template=template, context={"var": "🐍"}, expected="1")


def test_length_unicode_02(assert_render):
    template = "{{ var|length }}"
    assert_render(template=template, context={"var": "🐍"}, expected="1")


def test_length_undefined(assert_render):
    template = "{{ var|length }}"
    assert_render(template=template, context={}, expected="0")


def test_length_chained_with_bool(assert_render):
    template = "{% for x in 'ab' %}{{ forloop.first|length }}{% endfor %}"
    assert_render(template=template, context={}, expected="00")


def test_length_unexpected_argument(assert_parse_error):
    template = "{{ value|length:1 }}"

    django_message = "length requires 1 arguments, 2 provided"

    rusty_message = """\
  × length filter does not take an argument
   ╭────
 1 │ {{ value|length:1 }}
   ·                 ┬
   ·                 ╰── unexpected argument
   ╰────
"""

    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )
