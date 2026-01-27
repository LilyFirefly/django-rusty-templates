import pytest
from inline_snapshot import snapshot


@pytest.mark.parametrize(
    "template, expected",
    [
        ("{# this is hidden #}hello", "hello"),
        ("{# this is hidden #}hello{# foo #}", "hello"),
        ("foo{#  {% if %}  #}", "foo"),
        ("foo{#  {% endblock %}  #}", "foo"),
        ("foo{#  {% somerandomtag %}  #}", "foo"),
        ("foo{# {% #}", "foo"),
        ("foo{# %} #}", "foo"),
        ("foo{# %} #}bar", "foobar"),
        ("foo{# {{ #}", "foo"),
        ("foo{# }} #}", "foo"),
        ("foo{# { #}", "foo"),
        ("foo{# } #}", "foo"),
    ],
)
def test_comment_syntax(assert_render, template, expected):
    """
    Tests the {# ... #} comment syntax which is handled during lexing.
    """
    assert_render(
        template=template,
        context={},
        expected=expected,
    )


@pytest.mark.parametrize(
    "template, expected",
    [
        ("{% comment %}this is hidden{% endcomment %}hello", "hello"),
        (
            "{% comment %}this is hidden{% endcomment %}hello{% comment %}foo{% endcomment %}",
            "hello",
        ),
        ("foo{% comment %} {% if %} {% endcomment %}", "foo"),
        ("foo{% comment %} {% endblock %} {% endcomment %}", "foo"),
        ("foo{% comment %} {% somerandomtag %} {% endcomment %}", "foo"),
        ("{% comment %} {% comment %} inner {% endcomment %} outer", " outer"),
        ("{% comment %} endcommentary {% endcomment %}", ""),
        ("{% comment %}\n  multiline\n  {% endcomment %}", ""),
        ('{%  comment  "strict"  %}content{%   endcomment   %}', ""),
        ('{% comment arg1 arg2 "arg 3" %}content{% endcomment %}', ""),
        ("{% comment _('translated') %}content{% endcomment %}", ""),
        ("{% comment %} {{ var }} {% if %} {# comment #} {% endcomment %}", ""),
        ("{%comment%}no spaces{%endcomment%}", ""),
    ],
)
def test_comment_tag(assert_render, template, expected):
    """
    Tests the {% comment %} tag which is handled during parsing.
    """
    assert_render(
        template=template,
        context={},
        expected=expected,
    )


def test_unclosed_comment_tag(assert_parse_error):
    """
    Test that an unclosed comment tag raises the correct error.
    """
    template = "{% comment %} hidden stuff..."

    django_msg = "Unclosed tag on line 1: 'comment'. Looking for one of: endcomment."

    assert_parse_error(
        template=template,
        django_message=django_msg,
        rusty_message=snapshot("""\
  × Unclosed tag, expected endcomment
   ╭────
 1 │ {% comment %} hidden stuff...
   · ──────┬──────
   ·       ╰── this tag was never closed
   ╰────
"""),
    )


def test_comment_parsing_errors(assert_parse_error):
    """
    Test errors in the opening comment tag arguments.
    """
    template = '{% comment "unclosed string %}'
    django_msg = "Unclosed tag on line 1: 'comment'. Looking for one of: endcomment."
    assert_parse_error(
        template=template,
        django_message=django_msg,
        rusty_message=snapshot("""\
  × Expected a complete string literal
   ╭────
 1 │ {% comment "unclosed string %}
   ·            ────────┬───────
   ·                    ╰── here
   ╰────
"""),
    )

    # Invalid remainder (missing space)
    template = '{% comment "note"invalid %}'
    django_msg = "Unclosed tag on line 1: 'comment'. Looking for one of: endcomment."
    assert_parse_error(
        template=template,
        django_message=django_msg,
        rusty_message=snapshot("""\
  × Could not parse the remainder
   ╭────
 1 │ {% comment "note"invalid %}
   ·                  ───┬───
   ·                     ╰── here
   ╰────
"""),
    )
