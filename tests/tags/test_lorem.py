from django.utils.lorem_ipsum import COMMON_P, WORDS


def test_lorem_words(render_output):
    template = "{% lorem 3 w %}"
    output = render_output(
        template=template,
        context={},
    )
    assert "lorem ipsum dolor" == output


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
  × Expected an argument
   ╭────
 1 │ {% lorem 1 2 3 4 %}
   ·            ┬
   ·            ╰── here
   ╰────
"""

    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_lorem_single_word_default(render_output):
    template = "{% lorem w %}"
    output = render_output(template=template, context={})
    assert output == "lorem"


def test_lorem_single_paragraph_default(render_output):
    template = "{% lorem p %}"
    output = render_output(template=template, context={})
    assert output == f"<p>{COMMON_P}</p>"


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


def test_lorem_zero_count(render_output):
    template = "{% lorem 0 w %}"
    output = render_output(template=template, context={})
    assert output == ""


def test_lorem_duplicate_method(assert_parse_error):
    template = "{% lorem 2 w p %}"
    django_message = "Incorrect format for 'lorem' tag"
    rusty_message = """\
  × Expected an argument
   ╭────
 1 │ {% lorem 2 w p %}
   ·              ┬
   ·              ╰── here
   ╰────
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
  × Expected an argument
   ╭────
 1 │ {% lorem 2 p random random %}
   ·                     ───┬──
   ·                        ╰── here
   ╰────
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
  × Expected an argument
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
  × Expected an argument
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
