"""
Adapted from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_last.py
"""

import pytest
from inline_snapshot import snapshot
from django.utils.safestring import mark_safe


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ a|last }} {{ b|last }}",
            {"a": ["x", "a&b"], "b": ["x", mark_safe("a&b")]},
            "a&amp;b a&b",
            id="last01_autoescape_on",
        ),
        pytest.param(
            "{% autoescape off %}{{ a|last }} {{ b|last }}{% endautoescape %}",
            {"a": ["x", "a&b"], "b": ["x", mark_safe("a&b")]},
            "a&b a&b",
            id="last02_autoescape_off",
        ),
        pytest.param(
            "{% autoescape off %}{{ a|last }}{% endautoescape %}",
            {"a": []},
            "",
            id="last_empty_list",
        ),
    ],
)
def test_last(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_last_chained_with_forloop(assert_render_error):
    template = "{% for x in 'ab' %}{{ forloop.counter0|last }}{% endfor %}"
    assert_render_error(
        template=template,
        context={},
        exception=TypeError,
        django_message=snapshot("'int' object is not subscriptable"),
        rusty_message=snapshot("""\
  × 'int' object is not subscriptable
   ╭────
 1 │ {% for x in 'ab' %}{{ forloop.counter0|last }}{% endfor %}
   ·                                        ──┬─
   ·                                          ╰── here
   ╰────
"""),
    )


def test_last_chained_with_string(assert_render):
    template = "{% for x in 'ab' %}{{ x|last }}{% endfor %}"
    assert_render(template=template, context={}, expected="ab")


def test_last_unexpected_argument(assert_parse_error):
    rusty_message = snapshot("""\
  × last filter does not take an argument
   ╭────
 1 │ {{ bob|last:1 }}
   ·             ┬
   ·             ╰── unexpected argument
   ╰────
""")

    assert_parse_error(
        template="{{ bob|last:1 }}",
        django_message=snapshot("last requires 1 arguments, 2 provided"),
        rusty_message=rusty_message,
    )


def test_last_on_string(assert_render):
    assert_render(
        template="{{ value|last }}",
        context={"value": "hello"},
        expected="o",
    )


def test_last_on_integer(assert_render_error):
    assert_render_error(
        template="{{ value|last }}",
        context={"value": 123},
        exception=TypeError,
        django_message=snapshot("'int' object is not subscriptable"),
        rusty_message=snapshot("""\
  × 'int' object is not subscriptable
   ╭────
 1 │ {{ value|last }}
   ·          ──┬─
   ·            ╰── here
   ╰────
"""),
    )


def test_last_missing_variable(assert_render):
    assert_render(
        template="{{ missing|last }}",
        context={},
        expected="",
    )
