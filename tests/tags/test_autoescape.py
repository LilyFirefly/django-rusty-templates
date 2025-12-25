from inline_snapshot import snapshot


def test_autoescape_off(assert_render):
    html = "<p>Hello World!</p>"
    template = "{% autoescape off %}{{ html }}{% endautoescape %}"
    assert_render(template=template, context={"html": html}, expected=html)


def test_missing_argument(assert_parse_error):
    template = "{% autoescape %}{{ html }}"
    django_message = snapshot("'autoescape' tag requires exactly one argument.")
    rusty_message = snapshot("""\
  × 'autoescape' tag missing an 'on' or 'off' argument.
   ╭────
 1 │ {% autoescape %}{{ html }}
   ·              ▲
   ·              ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_argument(assert_parse_error):
    template = "{% autoescape foo %}{{ html }}"
    django_message = snapshot("'autoescape' argument should be 'on' or 'off'")
    rusty_message = snapshot("""\
  × 'autoescape' argument should be 'on' or 'off'.
   ╭────
 1 │ {% autoescape foo %}{{ html }}
   ·               ─┬─
   ·                ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extra_argument(assert_parse_error):
    template = "{% autoescape on off %}{{ html }}"
    django_message = snapshot("'autoescape' tag requires exactly one argument.")
    rusty_message = snapshot("""\
  × 'autoescape' tag requires exactly one argument.
   ╭────
 1 │ {% autoescape on off %}{{ html }}
   ·               ───┬──
   ·                  ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_endautoescape(assert_parse_error):
    template = "{% autoescape off %}{{ html }}"
    django_message = (
        "Unclosed tag on line 1: 'autoescape'. Looking for one of: endautoescape."
    )
    rusty_message = snapshot("""\
  × Unclosed 'autoescape' tag. Looking for one of: endautoescape
   ╭────
 1 │ {% autoescape off %}{{ html }}
   · ──────────┬─────────
   ·           ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_wrong_end_tag(assert_parse_error):
    template = "{% autoescape off %}{{ html }}{% endverbatim %}{% endautoescape %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endverbatim', expected 'endautoescape'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag endverbatim, expected endautoescape
   ╭────
 1 │ {% autoescape off %}{{ html }}{% endverbatim %}{% endautoescape %}
   · ──────────┬─────────          ────────┬────────
   ·           │                           ╰── unexpected tag
   ·           ╰── start tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_endautoescape_argument(assert_render):
    html = "<p>Hello World!</p>"
    template = "{% autoescape off %}{{ html }}{% endautoescape extra %}"
    assert_render(template=template, context={"html": html}, expected=html)


def test_nested_autoescape(assert_render):
    html = "<p>Hello World!</p>"
    template = "{{ html }}{% autoescape off %}{{ html }}{% autoescape on %}{{ html }}{% endautoescape %}{% endautoescape %}"
    escaped = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(
        template=template, context={"html": html}, expected=f"{escaped}{html}{escaped}"
    )


def test_autoescape_text(assert_render):
    template = "{% autoescape off %}<p>Hello World!</p>{% endautoescape %}"
    assert_render(template=template, context={}, expected="<p>Hello World!</p>")


def test_autoescape_comment(assert_render):
    template = "{% autoescape off %}{# comment #}{% endautoescape %}"
    assert_render(template=template, context={}, expected="")


def test_autoescape_url(assert_render):
    template = "{% autoescape off %}{% url 'home' %}{% endautoescape %}"
    assert_render(template=template, context={}, expected="/")


def test_unexpected_end_tag(assert_parse_error):
    template = "{% endautoescape %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endautoescape'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag endautoescape
   ╭────
 1 │ {% endautoescape %}
   · ─────────┬─────────
   ·          ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )
