from django.utils.lorem_ipsum import COMMON_P, WORDS


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


66


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


def test_lorem_method_before_count(assert_parse_error):
    template = "{% lorem p 2 %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Incorrect format for 'lorem' tag
   ╭────
 1 │ {% lorem p 2 %}
   ·            ┬
   ·            ╰── here
   ╰────
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
  × Incorrect format for 'lorem' tag
   ╭────
 1 │ {% lorem random 2 %}
   ·                 ┬
   ·                 ╰── here
   ╰────
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


def test_lorem_with_filter(render_output):
    template = "{% lorem count|default:3 w %}"
    output_default = render_output(template=template, context={})
    assert len(output_default.split(" ")) == 3

    output_provided = render_output(template=template, context={"count": 1})
    assert output_provided == "lorem"


def test_lorem_variable_count_plain(render_output):
    template = "{% lorem n w %}"
    output = render_output(
        template=template,
        context={"n": 4},
    )
    assert len(output.split(" ")) == 4
