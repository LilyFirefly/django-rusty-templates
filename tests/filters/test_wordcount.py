from inline_snapshot import snapshot
import pytest

from tests.utils import BrokenDunderStr


@pytest.mark.parametrize(
    "var,expected",
    [
        # Basic strings
        pytest.param("", "0", id="empty_string"),
        pytest.param("hello", "1", id="single_word"),
        pytest.param("hello world", "2", id="two_words"),
        pytest.param("The quick brown fox", "4", id="four_words"),
        # Whitespace variations
        pytest.param("  hello  world  ", "2", id="extra_spaces"),
        pytest.param("\thello\tworld\t", "2", id="tabs"),
        pytest.param("\nhello\nworld\n", "2", id="newlines"),
        pytest.param("hello\n\nworld", "2", id="multiple_newlines"),
        pytest.param("  ", "0", id="only_spaces"),
        pytest.param("\t\n", "0", id="only_whitespace"),
        # Punctuation
        pytest.param("hello-world", "1", id="hyphenated"),
        pytest.param("hello_world", "1", id="underscored"),
        pytest.param("hello.world", "1", id="dotted"),
        pytest.param("hello,world", "1", id="comma_separated"),
        # Unicode
        pytest.param("café résumé", "2", id="unicode"),
        pytest.param("hello мир 世界", "3", id="mixed_unicode"),
        # Types
        pytest.param(42, "1", id="integer"),
        pytest.param(3.14, "1", id="float"),
        pytest.param(True, "1", id="bool_true"),
        pytest.param(False, "1", id="bool_false"),
        # HTML
        pytest.param("<p>hello world</p>", "2", id="html_tags"),
    ],
)
def test_wordcount_basic(assert_render, var, expected):
    template = "{{ var|wordcount }}"
    assert_render(template=template, context={"var": var}, expected=expected)


def test_wordcount_undefined(assert_render):
    template = "{{ var|wordcount }}"
    assert_render(template=template, context={}, expected="0")


@pytest.mark.parametrize(
    "template,context,expected",
    [
        pytest.param(
            "{{ var|upper|wordcount }}",
            {"var": "hello world"},
            "2",
            id="chained_with_upper",
        ),
        pytest.param(
            "{{ var|default:'hello world'|wordcount }}",
            {},
            "2",
            id="chained_with_default",
        ),
        pytest.param(
            "{{ var|wordcount|add:5 }}",
            {"var": "hello world"},
            "7",
            id="chained_with_add",
        ),
        pytest.param(
            "{{ var|safe|wordcount }}",
            {"var": "<b>hello world</b>"},
            "2",
            id="safe_string",
        ),
    ],
)
def test_wordcount_chained(assert_render, template, context, expected):
    assert_render(template=template, context=context, expected=expected)


def test_wordcount_with_argument(assert_parse_error):
    template = "{{ var|wordcount:arg }}"
    django_message = snapshot("wordcount requires 1 arguments, 2 provided")
    rusty_message = snapshot("""\
  × wordcount filter does not take an argument
   ╭────
 1 │ {{ var|wordcount:arg }}
   ·                  ─┬─
   ·                   ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_wordcount_invalid_str_method(assert_render_error):
    broken = BrokenDunderStr()
    assert_render_error(
        template="{{ broken|wordcount }}",
        context={"broken": broken},
        exception=ZeroDivisionError,
        django_message=snapshot("division by zero"),
        rusty_message=snapshot("division by zero"),
    )
