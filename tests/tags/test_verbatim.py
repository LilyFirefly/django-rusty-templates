import pytest
from inline_snapshot import snapshot


@pytest.mark.parametrize(
    "template, expected",
    [
        (
            "{% verbatim x %}{% endverbatim %}{% endverbatim x %}{{ a }}",
            "{% endverbatim %}1",
        ),
        ("{% verbatim %}{% aaé %}{% endverbatim %}", "{% aaé %}"),
        ("{% verbatim %}{% xyzverbatim %}{% endverbatim %}", "{% xyzverbatim %}"),
        # https://docs.djangoproject.com/en/5.2/ref/templates/builtins/#verbatim
        (
            """\
{% verbatim %}
    {{if dying}}Still alive.{{/if}}
{% endverbatim %}""",
            "\n    {{if dying}}Still alive.{{/if}}\n",
        ),
        (
            """\
{% verbatim myblock %}
    Avoid template rendering via the {% verbatim %}{% endverbatim %} block.
{% endverbatim myblock %}""",
            "\n    Avoid template rendering via the {% verbatim %}{% endverbatim %} block.\n",
        ),
        # https://github.com/django/django/blob/main/tests/template_tests/syntax_tests/test_verbatim.py
        ("{% verbatim %}{{bare   }}{% endverbatim %}", "{{bare   }}"),
        ("{% verbatim %}{% endif %}{% endverbatim %}", "{% endif %}"),
        (
            "{% verbatim %}It's the {% verbatim %} tag{% endverbatim %}",
            "It's the {% verbatim %} tag",
        ),
        ("{% verbatim %}{% endverbatim %}{% verbatim %}{% endverbatim %}", ""),
        (
            "{% verbatim special %}"
            "Don't {% endverbatim %} just yet{% endverbatim special %}",
            "Don't {% endverbatim %} just yet",
        ),
        (
            "{% verbatim example %}\n{%\n{% endverbatim %}\n{% endverbatim example %}",
            "\n{%\n{% endverbatim %}\n",
        ),
        (
            "{% verbatim a  b %}{% endverbatim a b %}{% endverbatim a  b %}",
            "{% endverbatim a b %}",
        ),
        (
            "{% verbatim %}\n"
            "{% if user %}Hello, {{ user }}{% endif %}\n"
            "{% endverbatim %}",
            "\n{% if user %}Hello, {{ user }}{% endif %}\n",
        ),
        ("{% verbatim %}\n{%\n{% endverbatim %}", "\n{%\n"),
        ("{%verbatim%}{{ x }}{%endverbatim%}", "{{ x }}"),
        ("{% verbatim %}{{ x }}{%endverbatim%}", "{{ x }}"),
    ],
)
def test_verbatim(assert_render, template, expected):
    assert_render(template=template, context={"a": 1}, expected=expected)


def test_missing_endverbatim(assert_parse_error):
    template = "{% verbatim %}{{ a }}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'verbatim'. Looking for one of: endverbatim."
    )
    rusty_message = snapshot("""\
  × Unclosed 'verbatim' tag. Looking for one of: endverbatim
   ╭────
 1 │ {% verbatim %}{{ a }}
   · ───────┬──────
   ·        ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_named_endverbatim(assert_parse_error):
    template = "{% verbatim block %}{{ a }}{% endverbatim %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'verbatim'. Looking for one of: endverbatim."
    )
    rusty_message = snapshot("""\
  × Unclosed 'verbatim' tag. Looking for one of: endverbatim
   ╭────
 1 │ {% verbatim block %}{{ a }}{% endverbatim %}
   · ──────────┬─────────
   ·           ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extra_endverbatim(assert_parse_error):
    template = "{% verbatim %}{% verbatim %}{% endverbatim %}{% endverbatim %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endverbatim'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag endverbatim
   ╭────
 1 │ {% verbatim %}{% verbatim %}{% endverbatim %}{% endverbatim %}
   ·                                              ────────┬────────
   ·                                                      ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_empty_tag_swallows_endverbatim(assert_parse_error):
    template = "{% verbatim %}{%}{% endverbatim %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'verbatim'. Looking for one of: endverbatim."
    )
    rusty_message = snapshot("""\
  × Unclosed 'verbatim' tag. Looking for one of: endverbatim
   ╭────
 1 │ {% verbatim %}{%}{% endverbatim %}
   · ───────┬──────
   ·        ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )
