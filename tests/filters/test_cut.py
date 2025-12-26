"""
Adapted from
https://github.com/django/django/blob/5.1/tests/template_tests/filter_tests/test_cut.py
"""

from inline_snapshot import snapshot

import pytest
from django.utils.safestring import mark_safe
from django.template import VariableDoesNotExist


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            '{% autoescape off %}{{ a|cut:"x" }} {{ b|cut:"x" }}{% endautoescape %}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "&y &amp;y",
            id="cut01_autoescape_off",
        ),
        pytest.param(
            '{{ a|cut:"x" }} {{ b|cut:"x" }}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "&amp;y &amp;y",
            id="cut01_autoescape_on",
        ),
        pytest.param(
            '{% autoescape off %}{{ a|cut:"&" }} {{ b|cut:"&" }}{% endautoescape %}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "xy xamp;y",
            id="cut03_autoescape_off",
        ),
        pytest.param(
            '{{ a|cut:"&" }} {{ b|cut:"&" }}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "xy xamp;y",
            id="cut04_autoescape_on",
        ),
        pytest.param(
            '{% autoescape off %}{{ a|cut:";" }} {{ b|cut:";" }}{% endautoescape %}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "x&y x&ampy",
            id="cut05_autoescape_off",
        ),
        pytest.param(
            '{{ a|cut:";" }} {{ b|cut:";" }}',
            {"a": "x&y", "b": mark_safe("x&amp;y")},
            "x&amp;y x&amp;ampy",
            id="cut06_autoescape_on",
        ),
    ],
)
def test_cut(assert_render, template, context, expected):
    assert_render(template, context, expected)


def test_cut_for_character(assert_render):
    template = "{{ var|cut:'a' }}"
    context = {"var": "a string to be mangled"}
    expected = " string to be mngled"
    assert_render(template, context, expected)


def test_cut_for_characters(assert_render):
    template = "{{ var|cut:'ng'}}"
    context = {"var": "a string to be mangled"}
    expected = "a stri to be maled"
    assert_render(template, context, expected)


def test_cut_for_non_matching_string(assert_render):
    template = "{{ var|cut:'strings'}}"
    context = {"var": "a string to be mangled"}
    expected = "a string to be mangled"
    assert_render(template, context, expected)


def test_cut_for_non_string_input(assert_render):
    template = "{{ var|cut:'2'}}"
    context = {"var": 123}
    expected = "13"
    assert_render(template, context, expected)


def test_cut_for_no_variable(assert_render):
    template = "{{ var|cut:'a'}}"
    context = {"var": ""}
    expected = ""
    assert_render(template, context, expected)


def test_cut_for_missing_variable(assert_render):
    template = "{{ missing_var|cut:'a' }}"
    context = {}
    expected = ""
    assert_render(template, context, expected)


def test_cut_safe_string_non_semicolon(assert_render):
    template = "{{ var|cut:'x' }}"
    context = {"var": mark_safe("x&y")}
    expected = "&y"
    assert_render(template, context, expected)


def test_cut_for_explicit_none(assert_render):
    template = "{{ var|cut:'a' }}"
    context = {"var": None}
    expected = "None"
    assert_render(template, context, expected)


def test_cut_after_another_filter(assert_render):
    template = "{{ var|lower|cut:'x' }}"
    context = {"var": "X&Y"}
    expected = "&amp;y"
    assert_render(template, context, expected)


def test_cut_no_argument(assert_parse_error):
    django_message = snapshot("cut requires 2 arguments, 1 provided")
    rusty_message = snapshot("""\
  × Expected an argument
   ╭────
 1 │ {{var|cut}}
   ·       ─┬─
   ·        ╰── here
   ╰────
""")
    assert_parse_error(
        template="{{var|cut}}",
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_cut_error_missing_arg_variable(assert_render_error):
    template = "{{ var|cut:arg_var }}"
    context = {"var": "hello"}

    assert_render_error(
        template=template,
        context=context,
        exception=VariableDoesNotExist,
        django_message=snapshot(
            "Failed lookup for key [arg_var] in [{'True': True, 'False': False, 'None': None}, {'var': 'hello'}]"
        ),
        rusty_message=snapshot("""\
  × Failed lookup for key [arg_var] in {"False": False, "None": None, "True":
  │ True, "var": 'hello'}
   ╭────
 1 │ {{ var|cut:arg_var }}
   ·            ───┬───
   ·               ╰── key
   ╰────
"""),
    )


def test_cut_error_invalid_arg_type(assert_render_error):
    template = "{{ var|cut:bad_arg }}"
    context = {"var": "hello", "bad_arg": [1, 2, 3]}

    assert_render_error(
        template=template,
        context=context,
        exception=TypeError,
        rusty_exception=ValueError,
        django_message=snapshot("replace() argument 1 must be str, not list"),
        rusty_message=snapshot("""\
  × String argument expected
   ╭────
 1 │ {{ var|cut:bad_arg }}
   ·            ───┬───
   ·               ╰── here
   ╰────
"""),
    )


def test_cut_error_variable_conversion(assert_render_error):
    class Unstringable:
        def __str__(self):
            raise ValueError("Custom string conversion error")

    template = "{{ var|cut:'a' }}"
    context = {"var": Unstringable()}

    assert_render_error(
        template=template,
        context=context,
        exception=ValueError,
        django_message=snapshot("Custom string conversion error"),
        rusty_message=snapshot("Custom string conversion error"),
    )
