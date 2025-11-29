import pytest
from django.template.base import VariableDoesNotExist

from tests.utils import BrokenDunderStr


@pytest.mark.parametrize(
    "wordwrap_size,text,expected",
    [
        pytest.param(10, "Joel is a slug", "Joel is a\nslug", id="basic"),
        pytest.param(20, "short", "short", id="short_text"),
        pytest.param(5, "hello", "hello", id="exact_width"),
        pytest.param(5, "verylongword", "verylongword", id="long_word_not_broken"),
        pytest.param(
            10,
            "line one\nline two is longer",
            "line one\nline two\nis longer",
            id="preserves_line_breaks",
        ),
        pytest.param(10, "hello    world", "hello\nworld", id="multiple_spaces"),
        pytest.param(10, "", "", id="empty_string"),
        pytest.param(1, "a b c", "a\nb\nc", id="width_one"),
        pytest.param(10, "hello world\n", "hello\nworld\n", id="trailing_newline"),
        pytest.param(10, "   ", "   ", id="only_whitespace"),
        pytest.param(
            10, "hello\tworld world", "hello\nworld\nworld", id="tabs_and_spaces"
        ),
        pytest.param(10, "line1\n\nline2", "line1\n\nline2", id="multiple_newlines"),
        pytest.param(
            15,
            "The quick brown fox jumps over the lazy dog",
            "The quick brown\nfox jumps over\nthe lazy dog",
            id="long_text",
        ),
        pytest.param(
            10,
            "Hello, world! How are you?",
            "Hello,\nworld! How\nare you?",
            id="with_punctuation",
        ),
        pytest.param(
            5,
            "one two three four five",
            "one\ntwo\nthree\nfour\nfive",
            id="single_long_line",
        ),
        pytest.param(
            12,
            "a bb ccc dddd eeeee",
            "a bb ccc\ndddd eeeee",
            id="mixed_length_words",
        ),
        pytest.param(
            12,
            12345,
            "12345",
            id="number",
        ),
        pytest.param(
            12,
            "<b>hello world</b>",
            "&lt;b&gt;hello\nworld&lt;/b&gt;",
            id="html_escaped",
        ),
        pytest.param(
            14,
            "this is a long paragraph of text that really needs to be wrapped I'm afraid",
            "this is a long\nparagraph of\ntext that\nreally needs\nto be wrapped\nI&#x27;m afraid",
            id="long_paragraph",
        ),
        pytest.param(
            14,
            "this is a short paragraph of text.\n  But this line should be indented",
            "this is a\nshort\nparagraph of\ntext.\n  But this\nline should be\nindented",
            id="preserve_indent",
        ),
        pytest.param(
            15,
            "this is a short paragraph of text.\n  But this line should be indented",
            "this is a short\nparagraph of\ntext.\n  But this line\nshould be\nindented",
            id="preserve_indent_15",
        ),
        pytest.param(
            30,
            "this is a long paragraph of text that really needs to be wrapped\n\nthat is followed by another paragraph separated by an empty line\n",
            "this is a long paragraph of\ntext that really needs to be\nwrapped\n\nthat is followed by another\nparagraph separated by an\nempty line\n",
            id="preserve_empty_line",
        ),
        pytest.param(5, "\n\n\n", "\n\n\n", id="only_newlines"),
        pytest.param(5, "\n\n\n\n\n\n", "\n\n\n\n\n\n", id="many_newlines"),
        pytest.param(
            5,
            "first line\n     \nsecond line",
            "first\nline\n     \nsecond\nline",
            id="whitespace_only_line",
        ),
        pytest.param(
            5,
            "first line\n \t\t\t \nsecond line",
            "first\nline\n \t\t\t \nsecond\nline",
            id="mixed_whitespace_line",
        ),
        pytest.param(
            5,
            "first line\n     \nsecond line\n\nthird     \n",
            "first\nline\n     \nsecond\nline\n\nthird\n",
            id="complex_whitespace",
        ),
        pytest.param(
            5,
            "first line\n          \nsecond line",
            "first\nline\n          \nsecond\nline",
            id="double_width_spaces",
        ),
        pytest.param(
            9223372036854775808,
            "first line\n   \nsecond line",
            "first line\n   \nsecond line",
            id="very_large_integer",
        ),
    ],
)
def test_wordwrap(assert_render, wordwrap_size, text, expected):
    template = f"{{{{ text|wordwrap:{wordwrap_size} }}}}"
    assert_render(template, {"text": text}, expected)


def test_wordwrap_undefined(assert_render):
    template = "{{ text|wordwrap:10 }}"
    assert_render(template, {}, "")


def test_wordwrap_width_as_string(assert_render):
    template = "{{ text|wordwrap:'10' }}"
    assert_render(template, {"text": "Joel is a slug"}, "Joel is a\nslug")


def test_wordwrap_width_as_variable(assert_render):
    template = "{{ text|wordwrap:width }}"
    assert_render(template, {"text": "Joel is a slug", "width": 10}, "Joel is a\nslug")


def test_wordwrap_width_as_float(assert_render):
    template = "{{ text|wordwrap:10.7 }}"
    assert_render(template, {"text": "Joel is a slug"}, "Joel is a\nslug")


def test_wordwrap_with_autoescape_off(assert_render):
    template = (
        "{% autoescape off %}{{ a|wordwrap:3 }} {{ a|wordwrap:3 }}{% endautoescape %}"
    )
    assert_render(
        template,
        {"a": "a & b"},
        "a &\nb a &\nb",
    )


def test_wordwrap_very_long_text(template_engine):
    long_text = (
        "this is a long paragraph of text that really needs"
        " to be wrapped I'm afraid " * 20_000
    )
    template = template_engine.from_string("{{ text|wordwrap:10 }}")
    result = template.render({"text": long_text})

    # Verify the result contains the expected wrapped pattern
    expected_pattern = (
        "this is a\nlong\nparagraph\nof text\nthat\nreally\nneeds to\nbe wrapped"
    )
    assert expected_pattern in result


def test_wordwrap_with_safe(assert_render):
    template = "{{ a|wordwrap:3 }} {{ b|safe|wordwrap:3 }}"
    assert_render(
        template,
        {"a": "a & b", "b": "a & b"},
        "a &amp;\nb a &\nb",
    )


def test_wordwrap_no_argument(assert_parse_error):
    assert_parse_error(
        template="{{ text|wordwrap }}",
        django_message="wordwrap requires 2 arguments, 1 provided",
        rusty_message="""\
  × Expected an argument
   ╭────
 1 │ {{ text|wordwrap }}
   ·         ────┬───
   ·             ╰── here
   ╰────
""",
    )


def test_wordwrap_invalid_width_string(assert_render_error):
    assert_render_error(
        template="{{ text|wordwrap:'invalid' }}",
        context={"text": "hello"},
        exception=ValueError,
        django_message="invalid literal for int() with base 10: 'invalid'",
        rusty_message="""\
  × Couldn't convert argument ('invalid') to integer
   ╭────
 1 │ {{ text|wordwrap:'invalid' }}
   ·                  ────┬────
   ·                      ╰── argument
   ╰────
""",
    )


def test_wordwrap_negative_width(assert_render_error):
    rusty_message = """\
  × invalid width -5 (must be > 0)
   ╭────
 1 │ {{ text|wordwrap:-5 }}
   ·                  ─┬
   ·                   ╰── width
   ╰────
"""
    assert_render_error(
        template="{{ text|wordwrap:-5 }}",
        context={"text": "hello world"},
        exception=ValueError,
        django_message="invalid width -5 (must be > 0)",
        rusty_message=rusty_message,
    )


def test_wordwrap_bool_zero_width(assert_render_error):
    rusty_message = """\
  × invalid width 0 (must be > 0)
   ╭────
 1 │ {{ text|wordwrap:False }}
   ·                  ──┬──
   ·                    ╰── width
   ╰────
"""
    assert_render_error(
        template="{{ text|wordwrap:False }}",
        context={"text": "hello world"},
        exception=ValueError,
        django_message="invalid width 0 (must be > 0)",
        rusty_message=rusty_message,
    )


def test_wordwrap_zero_width(assert_render_error):
    rusty_message = """\
  × invalid width 0 (must be > 0)
   ╭────
 1 │ {{ text|wordwrap:0 }}
   ·                  ┬
   ·                  ╰── width
   ╰────
"""
    assert_render_error(
        template="{{ text|wordwrap:0 }}",
        context={"text": "hello world"},
        exception=ValueError,
        django_message="invalid width 0 (must be > 0)",
        rusty_message=rusty_message,
    )


def test_wordwrap_width_overflow_float(assert_render_error):
    assert_render_error(
        template="{{ text|wordwrap:1e310 }}",
        context={"text": "hello"},
        exception=OverflowError,
        django_message="cannot convert float infinity to integer",
        rusty_message="""\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ text|wordwrap:1e310 }}
   ·                  ──┬──
   ·                    ╰── here
   ╰────
""",
    )


def test_wordwrap_width_float_overflow(assert_render_error):
    assert_render_error(
        template="{{ text|wordwrap:1e310 }}",
        context={"text": "hello"},
        exception=OverflowError,
        django_message="cannot convert float infinity to integer",
        rusty_message="""\
  × Couldn't convert float (inf) to integer
   ╭────
 1 │ {{ text|wordwrap:1e310 }}
   ·                  ──┬──
   ·                    ╰── here
   ╰────
""",
    )


def test_wordwrap_width_from_python_variable(assert_render_error):
    assert_render_error(
        template="{{ text|wordwrap:width }}",
        context={"text": "hello", "width": "not a number"},
        exception=ValueError,
        django_message="invalid literal for int() with base 10: 'not a number'",
        rusty_message="""\
  × Couldn't convert argument (not a number) to integer
   ╭────
 1 │ {{ text|wordwrap:width }}
   ·                  ──┬──
   ·                    ╰── argument
   ╰────
""",
    )


def test_wordwrap_missing_width_argument(assert_render_error):
    django_message = "Failed lookup for key [width] in [{'True': True, 'False': False, 'None': None}, {'text': 'hello'}]"
    rusty_message = """\
  × Failed lookup for key [width] in {"False": False, "None": None, "True":
  │ True, "text": 'hello'}
   ╭────
 1 │ {{ text|wordwrap:width }}
   ·                  ──┬──
   ·                    ╰── key
   ╰────
"""
    assert_render_error(
        template="{{ text|wordwrap:width }}",
        context={"text": "hello"},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_wordwrap_invalid_str_method(assert_render_error):
    broken = BrokenDunderStr()
    assert_render_error(
        template="{{ broken|wordwrap:1 }}",
        context={"broken": broken},
        exception=ZeroDivisionError,
        django_message="division by zero",
        rusty_message="division by zero",
    )
