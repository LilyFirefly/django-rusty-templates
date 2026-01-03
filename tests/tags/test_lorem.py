import pytest
from django.utils.lorem_ipsum import COMMON_P, WORDS, COMMON_WORDS


def test_lorem_words(assert_render):
    template = "{% lorem 3 w %}"
    assert_render(template=template, context={}, expected="lorem ipsum dolor")


def test_lorem_random(render_output):
    template = "{% lorem 3 w random %}"
    output = render_output(template=template, context={})

    words = output.split(" ")
    assert len(words) == 3
    for word in words:
        assert word in WORDS


def test_lorem_default(assert_render):
    template = "{% lorem %}"
    assert_render(
        template=template,
        context={},
        expected=COMMON_P,
    )


def test_lorem_multiple_paragraphs(render_output):
    template = "{% lorem 2 p %}"
    output = render_output(template=template, context={})
    assert output.count("<p>") == 2


def test_lorem_incorrect_count(render_output):
    template = "{% lorem two p %}"
    output = render_output(template=template, context={})
    assert output.count("<p>") == 1


def test_lorem_syntax_error(assert_parse_error):
    template = "{% lorem 1 2 3 4 %}"

    django_message = "Incorrect format for 'lorem' tag"

    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'count' argument was provided more than
  │ once
   ╭────
 1 │ {% lorem 1 2 3 4 %}
   ·          ┬ ┬
   ·          │ ╰── second 'count'
   ·          ╰── first 'count'
   ╰────
  help: Try removing the second 'count'
"""

    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_single_word_default(assert_render):
    template = "{% lorem w %}"
    assert_render(template=template, context={}, expected="lorem")


def test_lorem_single_paragraph_default(assert_render):
    template = "{% lorem p %}"
    assert_render(template=template, context={}, expected=f"<p>{COMMON_P}</p>")


def test_lorem_blocks(render_output):
    template = "{% lorem 2 b %}"
    output = render_output(template=template, context={})
    assert output.count(COMMON_P.split()[0]) >= 1
    assert output.count("\n\n") == 1


def test_lorem_random_paragraphs(render_output):
    template = "{% lorem 2 p random %}"
    output = render_output(template=template, context={})
    assert COMMON_P not in output
    assert output.count("<p>") == 2


def test_lorem_zero_count(assert_render):
    template = "{% lorem 0 w %}"
    assert_render(template=template, context={}, expected="")


def test_lorem_duplicate_method(assert_parse_error):
    template = "{% lorem 2 w p %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'method' argument was provided more than
  │ once
   ╭────
 1 │ {% lorem 2 w p %}
   ·            ┬ ┬
   ·            │ ╰── second 'method'
   ·            ╰── first 'method'
   ╰────
  help: Try removing the second 'method'
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_duplicate_method_with_method_as_count(assert_parse_error):
    template = "{% lorem b w p %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'method' argument was provided more than
  │ once
   ╭────
 1 │ {% lorem b w p %}
   ·            ┬ ┬
   ·            │ ╰── second 'method'
   ·            ╰── first 'method'
   ╰────
  help: Try removing the second 'method'
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_duplicate_random(assert_parse_error):
    template = "{% lorem 2 p random random %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'random' was provided more than once
   ╭────
 1 │ {% lorem 2 p random random %}
   ·              ───┬── ───┬──
   ·                 │      ╰── second 'random'
   ·                 ╰── first 'random'
   ╰────
  help: Try removing the second 'random'
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_duplicate_random_with_random_as_count(assert_parse_error):
    template = "{% lorem random random random %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'random' was provided more than once
   ╭────
 1 │ {% lorem random random random %}
   ·                 ───┬── ───┬──
   ·                    │      ╰── second 'random'
   ·                    ╰── first 'random'
   ╰────
  help: Try removing the second 'random'
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_method_before_count(assert_parse_error):
    template = "{% lorem p 2 %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'count' must come before the 'method'
  │ argument
   ╭────
 1 │ {% lorem p 2 %}
   ·          ┬ ┬
   ·          │ ╰── count
   ·          ╰── method
   ╰────
  help: Move the 'count' argument before the 'method' argument
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_random_before_count(assert_parse_error):
    template = "{% lorem random 2 %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'count' must come before the 'random'
  │ argument
   ╭────
 1 │ {% lorem random 2 %}
   ·          ───┬── ┬
   ·             │   ╰── count
   ·             ╰── random
   ╰────
  help: Move the 'count' argument before the 'random' argument
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_random_before_method(assert_parse_error):
    template = "{% lorem 2 random p %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag: 'method' must come before the 'random'
  │ argument
   ╭────
 1 │ {% lorem 2 random p %}
   ·            ───┬── ┬
   ·               │   ╰── method
   ·               ╰── random
   ╰────
  help: Move the 'method' argument before the 'random' argument
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_keyword_as_variable(render_output):
    template = "{% lorem w w %}"
    output = render_output(
        template=template,
        context={"w": 5},
    )
    assert len(output.split(" ")) == 5


def test_lorem_random_as_variable(render_output):
    template = "{% lorem random w %}"
    output = render_output(
        template=template,
        context={"random": 2},
    )
    assert len(output.split(" ")) == 2


def test_lorem_random_as_variable_before_random(render_output):
    template = "{% lorem random random %}"
    output = render_output(
        template=template,
        context={"random": 2},
    )
    assert len(output.split("\n\n")) == 2


@pytest.mark.parametrize(
    "context,expected_words",
    [
        ({}, 3),
        ({"count": 1}, 1),
    ],
)
def test_lorem_with_filter(render_output, context, expected_words):
    template = "{% lorem count|default:3 w %}"
    output = render_output(template=template, context=context)
    assert len(output.split(" ")) == expected_words


def test_lorem_variable_count_plain(render_output):
    template = "{% lorem n w %}"
    output = render_output(
        template=template,
        context={"n": 4},
    )
    assert len(output.split(" ")) == 4


def test_lorem_missing_variable_defaults_to_one(render_output):
    template = "{% lorem missing_var w %}"
    output = render_output(template=template, context={})
    assert output == "lorem"


@pytest.mark.parametrize(
    "context,expected",
    [
        ({"val": 1}, 3),
        ({}, 5),
    ],
)
def test_lorem_with_complex_filter_parsing(render_output, context, expected):
    template = "{% lorem val|add:2|default:5 w %}"
    output_a = render_output(template=template, context=context)
    assert len(output_a.split(" ")) == expected


def test_lorem_parser_error_propagation(assert_parse_error):
    template = "{% lorem n|invalid_filter %}"

    django_message = "Invalid filter: 'invalid_filter'"

    rusty_message = """\
  × Invalid filter: 'invalid_filter'
   ╭────
 1 │ {% lorem n|invalid_filter %}
   ·            ───────┬──────
   ·                   ╰── here
   ╰────
"""

    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_parser_error_propagation_2(assert_parse_error):
    template = "{% lorem Count| %}"

    django_message = "Could not parse the remainder: '|' from 'Count|'"

    rusty_message = """\
  × Could not parse the remainder
   ╭────
 1 │ {% lorem Count| %}
   ·               ┬
   ·               ╰── here
   ╰────
"""

    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_variable_float_coercion(render_output):
    template = "{% lorem count w %}"
    output = render_output(template=template, context={"count": 5.9})
    words = output.split(" ")
    assert len(words) in [1, 5]


def test_lorem_variable_string_number(render_output):
    template = "{% lorem count w %}"
    output = render_output(template=template, context={"count": "5"})
    assert len(output.split(" ")) == 5


def test_lorem_variable_invalid_type_defaults(render_output):
    template = "{% lorem count w %}"
    output = render_output(template=template, context={"count": [1, 2, 3]})
    assert output == "lorem"


def test_lorem_with_filter_returning_none(render_output):
    template = "{% lorem val|yesno:'1,' w %}"
    output = render_output(template=template, context={"val": False})
    assert output == "lorem"


def test_lorem_string_garbage_defaults_to_one(render_output):
    """A string that isn't a number should default to 1."""
    template = "{% lorem count w %}"
    output = render_output(template=template, context={"count": "abc"})
    assert output == "lorem"


# def test_lorem_extreme_count_defaults_to_one(render_output):
#     # A number way larger than a 64-bit integer
#     template = "{% lorem 99999999999999999999999999999999999999 w %}"
#     output = render_output(template=template, context={})
#     assert output == "lorem"


def test_lorem_boolean_true_count(render_output):
    template_true = "{% lorem val_true w %}"
    output_true = render_output(template=template_true, context={"val_true": True})
    assert output_true == "lorem"


def test_lorem_boolean_false_count(render_output):
    template_false = "{% lorem val_false w %}"
    output_false = render_output(template=template_false, context={"val_false": False})
    assert output_false == ""


def test_lorem_common_extension_logic(render_output):
    template = "{% lorem 20 w %}"
    output = render_output(template=template, context={})
    words_list = output.split(" ")

    assert len(words_list) == 20

    assert words_list[:19] == list(COMMON_WORDS)


def test_lorem_with_negative_count(render_output):
    template = "{% lorem -5 %}"
    output = render_output(template=template, context={})
    assert output == ""


def test_lorem_words_with_negative_count(render_output):
    template = "{% lorem -5 w %}"
    output = render_output(template=template, context={})
    assert output == " ".join(COMMON_WORDS[:-5])
