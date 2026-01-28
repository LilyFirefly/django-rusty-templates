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
  × Unclosed 'comment' tag. Looking for one of: endcomment
   ╭────
 1 │ {% comment %} hidden stuff...
   · ──────┬──────
   ·       ╰── started here
   ╰────
"""),
    )


def test_comment_invalid_opening_tag_success(assert_render):
    """
    Invalid content in the opening comment tag is ignored if closed.
    """
    assert_render(
        template='{% comment "note"invalid %}content{% endcomment %}',
        context={},
        expected="",
    )


def test_comment_invalid_remainder_error(assert_parse_error):
    """
    Invalid remainder in opening comment tag reports as unclosed if unclosed.
    """
    template = '{% comment "note"invalid %}'
    django_msg = "Unclosed tag on line 1: 'comment'. Looking for one of: endcomment."
    assert_parse_error(
        template=template,
        django_message=django_msg,
        rusty_message=snapshot("""\
  × Unclosed 'comment' tag. Looking for one of: endcomment
   ╭────
 1 │ {% comment "note"invalid %}
   · ─────────────┬─────────────
   ·              ╰── started here
   ╰────
"""),
    )


def test_comment_unclosed_string_error(assert_parse_error):
    """
    Unclosed string in opening comment tag reports as unclosed if unclosed.
    """
    template = '{% comment "unclosed string %}'
    django_msg = "Unclosed tag on line 1: 'comment'. Looking for one of: endcomment."
    assert_parse_error(
        template=template,
        django_message=django_msg,
        rusty_message=snapshot("""\
  × Unclosed 'comment' tag. Looking for one of: endcomment
   ╭────
 1 │ {% comment "unclosed string %}
   · ───────────────┬──────────────
   ·                ╰── started here
   ╰────
"""),
    )
