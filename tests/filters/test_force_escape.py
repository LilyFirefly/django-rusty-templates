from inline_snapshot import snapshot


def test_force_escape(assert_render):
    template = "{{ a|force_escape }}"
    a = "x&y"
    escaped = "x&amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_force_escape_missing_value(assert_render):
    template = "{{ value|force_escape }}"
    context = {}
    assert_render(template, context, "")


def test_force_escape_with_argument(assert_parse_error):
    template = "{{ value|force_escape:invalid }}"
    django_message = snapshot("force_escape requires 1 arguments, 2 provided")
    rusty_message = snapshot("""\
  × force_escape filter does not take an argument
   ╭────
 1 │ {{ value|force_escape:invalid }}
   ·                       ───┬───
   ·                          ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_force_escape_in_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ a|force_escape }}{% endautoescape %}"
    a = "x&y"
    escaped = "x&amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_force_escape_in_autoescape_on(assert_render):
    template = "{% autoescape on %}{{ a|force_escape }}{% endautoescape %}"
    a = "x&y"
    escaped = "x&amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_chaining_force_escape(assert_render):
    template = "{{ a|force_escape|force_escape }}"
    a = "x&y"
    escaped = "x&amp;amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_chaining_force_escape_in_autoescape_off(assert_render):
    template = (
        "{% autoescape off %}{{ a|force_escape|force_escape }}{% endautoescape %}"
    )
    a = "x&y"
    escaped = "x&amp;amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_escape_after_force_escape_is_noop(assert_render):
    template = "{{ a|force_escape|escape }}"
    a = "x&y"
    escaped = "x&amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_escape_after_force_escape_in_autoescape_off_is_noop(assert_render):
    template = "{% autoescape off %}{{ a|force_escape|escape }}{% endautoescape %}"
    a = "x&y"
    escaped = "x&amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_force_escape_after_escape(assert_render):
    template = "{{ a|escape|force_escape }}"
    a = "x&y"
    escaped = "x&amp;amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)


def test_force_escape_after_escape_in_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ a|escape|force_escape }}{% endautoescape %}"
    a = "x&y"
    escaped = "x&amp;amp;y"
    assert_render(template=template, context={"a": a}, expected=escaped)
