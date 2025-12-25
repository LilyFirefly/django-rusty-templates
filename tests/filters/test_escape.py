from inline_snapshot import snapshot


def test_escape(assert_render):
    template = "{{ html|escape }}"
    html = "<p>Hello World!</p>"
    escaped = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=escaped)


def test_escape_with_argument(assert_parse_error):
    template = "{{ html|escape:invalid }}"
    django_message = snapshot("escape requires 1 arguments, 2 provided")
    rusty_message = snapshot("""\
  × escape filter does not take an argument
   ╭────
 1 │ {{ html|escape:invalid }}
   ·                ───┬───
   ·                   ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_escape_missing_value(assert_render):
    template = "{{ html|escape }}"
    assert_render(template=template, context={}, expected="")


def test_already_escaped(assert_render):
    template = "{{ html|escape|escape }}"
    html = "<p>Hello World!</p>"
    escaped = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=escaped)


def test_escape_integer(assert_render):
    template = "{{ num|default:100|escape }}"
    assert_render(template=template, context={}, expected="100")


def test_escape_float(assert_render):
    template = "{{ num|default:1.6|escape }}"
    assert_render(template=template, context={}, expected="1.6")


def test_escape_bool(assert_render):
    template = "{% for x in 'xy' %}{{ forloop.first|escape }}{% endfor %}"
    assert_render(template=template, context={}, expected="TrueFalse")


def test_escape_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ html|escape }}{% endautoescape %}"
    html = "<p>Hello World!</p>"
    escaped = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=escaped)


def test_escape_autoescape_off_lower(assert_render):
    template = "{% autoescape off %}{{ html|lower|escape }}{% endautoescape %}"
    html = "<p>Hello World!</p>"
    escaped = "&lt;p&gt;hello world!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=escaped)
