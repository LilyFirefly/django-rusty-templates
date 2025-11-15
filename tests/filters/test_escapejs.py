"""
Test cases for the escapejs filter.
The escapejs filter escapes characters for use in JavaScript strings.
"""

import pytest


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("test", "test", id="simple_string"),
        pytest.param("", "", id="empty_string"),
        pytest.param(123, "123", id="integer"),
        pytest.param(1.5, "1.5", id="float"),
        pytest.param(True, "True", id="bool_true"),
        pytest.param(False, "False", id="bool_false"),
        pytest.param("café", "café", id="unicode"),
        pytest.param("Hello 👋", "Hello 👋", id="emoji"),
        pytest.param("hello world", "hello world", id="string_with_space"),
        pytest.param(
            "'single quotes'", r"\u0027single quotes\u0027", id="single_quotes"
        ),
        pytest.param(
            '"double quotes"', r"\u0022double quotes\u0022", id="double_quotes"
        ),
        pytest.param(r"back\slash", r"back\u005Cslash", id="backslash"),
        pytest.param("<script>", r"\u003Cscript\u003E", id="script_tags"),
        pytest.param("a&b", r"a\u0026b", id="ampersand"),
        pytest.param("a=b", r"a\u003Db", id="equals"),
        pytest.param("a-b", r"a\u002Db", id="hyphen"),
        pytest.param("a;b", r"a\u003Bb", id="semicolon"),
        pytest.param("`backtick`", r"\u0060backtick\u0060", id="backtick"),
        pytest.param("\u2028", r"\u2028", id="line_separator"),
        pytest.param("\u2029", r"\u2029", id="paragraph_separator"),
        pytest.param("\n", r"\u000A", id="newline"),
        pytest.param("\r", r"\u000D", id="carriage_return"),
        pytest.param("\t", r"\u0009", id="tab"),
        pytest.param(
            "Line 1\nLine 2\tTabbed",
            r"Line 1\u000ALine 2\u0009Tabbed",
            id="mixed_tab_newline",
        ),
        pytest.param("\x00", r"\u0000", id="null_character"),
        pytest.param("\x1f", r"\u001F", id="control_character"),
        pytest.param("\x01", r"\u0001", id="control_soh"),
        pytest.param("\x1b", r"\u001B", id="control_escape"),
        pytest.param(
            "<script>alert('XSS')</script>",
            r"\u003Cscript\u003Ealert(\u0027XSS\u0027)\u003C/script\u003E",
            id="xss_attempt",
        ),
        pytest.param(
            "a'b\"c\\d<e>f&g=h-i;j`k",
            r"a\u0027b\u0022c\u005Cd\u003Ce\u003Ef\u0026g\u003Dh\u002Di\u003Bj\u0060k",
            id="multiple_special_chars",
        ),
    ],
)
def test_escapejs(assert_render, value, expected):
    template = "{{ value|escapejs }}"
    context = {"value": value}
    assert_render(template, context, expected)


def test_escapejs_missing_value(assert_render):
    template = "{{ value|escapejs }}"
    context = {}
    assert_render(template, context, "")


def test_escapejs_chained_with_lower(assert_render):
    template = "{{ value|lower|escapejs }}"
    context = {"value": "HELLO<WORLD>"}
    assert_render(template, context, r"hello\u003Cworld\u003E")


@pytest.mark.parametrize(
    "value,expected",
    [
        pytest.param("\x7f", r"\u007F", id="del_not_escaped"),
        pytest.param("\x80", r"\u0080", id="c1_control_not_escaped"),
    ],
)
def test_escapejs_c1_control_characters(
    assert_render, template_engine, value, expected
):
    if template_engine.name == "django":
        pytest.skip(
            "Django escapejs only escape C0 controls, not C1 controls"
            "See https://en.wikipedia.org/wiki/C0_and_C1_control_codes#C1_controls"
        )

    template = "{{ value|escapejs }}"
    context = {"value": value}
    assert_render(template, context, expected)


def test_escapejs_with_argument(assert_parse_error):
    template = "{{ value|escapejs:invalid }}"
    django_message = "escapejs requires 1 arguments, 2 provided"
    rusty_message = """\
  × escapejs filter does not take an argument
   ╭────
 1 │ {{ value|escapejs:invalid }}
   ·                   ───┬───
   ·                      ╰── unexpected argument
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )
