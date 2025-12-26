from inline_snapshot import snapshot


def test_safe(assert_render):
    template = "{{ html|safe }}"
    html = "<p>Hello World!</p>"
    assert_render(template=template, context={"html": html}, expected=html)


def test_safe_with_argument(assert_parse_error):
    template = "{{ html|safe:invalid }}"
    django_message = snapshot("safe requires 1 arguments, 2 provided")
    rusty_message = snapshot("""\
  × safe filter does not take an argument
   ╭────
 1 │ {{ html|safe:invalid }}
   ·              ───┬───
   ·                 ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_safe_missing_value(assert_render):
    template = "{{ html|safe }}"
    assert_render(template=template, context={}, expected="")


def test_safe_already_safe(assert_render):
    template = "{{ html|safe|safe }}"
    html = "<p>Hello World!</p>"
    assert_render(template=template, context={"html": html}, expected=html)


def test_safe_integer(assert_render):
    template = "{{ num|default:100|safe }}"
    assert_render(template=template, context={}, expected="100")


def test_safe_float(assert_render):
    template = "{{ num|default:1.6|safe }}"
    assert_render(template=template, context={}, expected="1.6")


def test_safe_escaped(assert_render):
    template = "{{ html|escape|safe }}"
    html = "<p>Hello World!</p>"
    escaped = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=escaped)


def test_safe_bool(assert_render):
    template = "{% for x in 'xy' %}{{ forloop.first|safe }}{% endfor %}"
    assert_render(template=template, context={}, expected="TrueFalse")


def test_safe_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ html|safe }}{% endautoescape %}"
    html = "<p>Hello World!</p>"
    assert_render(template=template, context={"html": html}, expected=html)


def test_safe_autoescape_off_lower(assert_render):
    template = "{% autoescape off %}{{ html|lower|safe }}{% endautoescape %}"
    html = "<p>Hello World!</p>"
    assert_render(template=template, context={"html": html}, expected=html.lower())
