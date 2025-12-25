from inline_snapshot import snapshot


def test_upper_string(assert_render):
    template = "{{ var|upper }}"
    var = "foo"
    uppered = "FOO"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_undefined(assert_render):
    template = "{{ var|upper }}"
    assert_render(template=template, context={}, expected="")


def test_upper_integer(assert_render):
    template = "{{ var|upper }}"
    var = "3"
    uppered = "3"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_with_argument(assert_parse_error):
    template = "{{ var|upper:arg }}"
    django_message = snapshot("upper requires 1 arguments, 2 provided")
    rusty_message = snapshot("""\
  × upper filter does not take an argument
   ╭────
 1 │ {{ var|upper:arg }}
   ·              ─┬─
   ·               ╰── unexpected argument
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_upper_unicode(assert_render):
    template = "{{ var|upper }}"
    var = "\xeb"
    uppered = "\xcb"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_html(assert_render):
    template = "{{ var|upper }}"
    var = "<b>foo</b>"
    uppered = "&lt;B&gt;FOO&lt;/B&gt;"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_html_safe(assert_render):
    template = "{{ var|upper|safe }}"
    var = "<b>foo</b>"
    uppered = "<B>FOO</B>"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_add_strings(assert_render):
    template = "{{ var|upper|add:'bar' }}"
    var = "var"
    uppered = "VARbar"
    assert_render(template=template, context={"var": var}, expected=uppered)


def test_upper_add_numbers(assert_render):
    template = "{{ var|upper|add:4 }}"
    var = "2"
    uppered = "6"
    assert_render(template=template, context={"var": var}, expected=uppered)
