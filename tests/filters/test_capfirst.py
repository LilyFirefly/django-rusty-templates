"""
Adapted from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_capfirst.py
"""

from inline_snapshot import snapshot

import pytest
from django.utils.safestring import mark_safe


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{% autoescape off %}{{ a|capfirst }} {{ b|capfirst }}{% endautoescape %}",
            {"a": "fred>", "b": mark_safe("fred&gt;")},
            "Fred> Fred&gt;",
            id="capfirst01_autoescape_off",
        ),
        pytest.param(
            "{{ a|capfirst }} {{ b|capfirst }}",
            {"a": "fred>", "b": mark_safe("fred&gt;")},
            "Fred&gt; Fred&gt;",
            id="capfirst02_autoescape_on",
        ),
        pytest.param(
            "{{ a|capfirst }}",
            {"a": "hello world"},
            "Hello world",
            id="capfirst_basic",
        ),
        pytest.param(
            "{{ a|capfirst }}",
            {"a": ["hello"]},
            "[&#x27;hello&#x27;]",
            id="capfirst_for_list",
        ),
    ],
)
def test_capfirst(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_capfirst_chained_with_bool(assert_render):
    template = "{% for x in 'ab' %}{{ forloop.first|capfirst }}{% endfor %}"
    assert_render(template=template, context={}, expected="TrueFalse")


def test_capfirt_unexpected_argument(assert_parse_error):
    rusty_message = snapshot("""\
  × capfirst filter does not take an argument
   ╭────
 1 │ {{bob|capfirst:1}}
   ·                ┬
   ·                ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template="{{bob|capfirst:1}}",
        django_message=snapshot("capfirst requires 1 arguments, 2 provided"),
        rusty_message=rusty_message,
    )


@pytest.mark.parametrize(
    "template,value,expected",
    [
        pytest.param("{{ v|capfirst|length }}", "a<b", "3", id="capfirst_then_length"),
        pytest.param(
            "{{ v|capfirst|slugify }}", 'a"b', "ab", id="capfirst_then_slugify"
        ),
        pytest.param("{{ v|capfirst }}", "a<b", "A&lt;b", id="capfirst_escapes_once"),
        pytest.param(
            "{{ v|capfirst }}", mark_safe("<b>"), "<b>", id="capfirst_keeps_safe"
        ),
    ],
)
def test_capfirst_does_not_escape_early(assert_render, template, value, expected):
    assert_render(template=template, context={"v": value}, expected=expected)
