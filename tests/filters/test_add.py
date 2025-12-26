from inline_snapshot import snapshot
from django.template.base import VariableDoesNotExist


def test_add_integers(assert_render):
    template = "{{ foo|add:3 }}"
    assert_render(template=template, context={"foo": 2}, expected="5")


def test_add_no_variable(assert_render):
    template = "{{ foo|add:3 }}"
    assert_render(template=template, context={}, expected="")


def test_add_no_argument(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [bar] in [{'True': True, 'False': False, 'None': None}, {'foo': 1}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [bar] in {"False": False, "None": None, "True":
  │ True, "foo": 1}
   ╭────
 1 │ {{ foo|add:bar }}
   ·            ─┬─
   ·             ╰── key
   ╰────
""")
    assert_render_error(
        template="{{ foo|add:bar }}",
        context={"foo": 1},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_add_integer_strings(assert_render):
    template = "{{ foo|add:'3' }}"
    assert_render(template=template, context={"foo": "2"}, expected="5")


def test_add_strings(assert_render):
    template = "{{ foo|add:'def' }}"
    assert_render(template=template, context={"foo": "abc"}, expected="abcdef")


def test_add_lists(assert_render):
    template = "{{ foo|add:bar}}"
    assert_render(
        template=template, context={"foo": [1], "bar": [2]}, expected="[1, 2]"
    )


def test_add_incompatible(assert_render):
    template = "{{ foo|add:bar}}"
    assert_render(template=template, context={"foo": [1], "bar": 2}, expected="")


def test_add_float(assert_render):
    template = "{{ foo|add:bar}}"
    assert_render(template=template, context={"foo": 1.2, "bar": 2.9}, expected="3")


def test_add_float_literal(assert_render):
    template = "{{ foo|add:2.9 }}"
    assert_render(template=template, context={"foo": 1.2}, expected="3")


def test_add_incompatible_int(assert_render):
    template = "{{ foo|add:2}}"
    assert_render(template=template, context={"foo": [1]}, expected="")


def test_add_incompatible_float(assert_render):
    template = "{{ foo|add:2.9}}"
    assert_render(template=template, context={"foo": [1]}, expected="")


def test_add_missing_argument(assert_parse_error):
    template = "{{ foo|add }}"
    django_message = snapshot("add requires 2 arguments, 1 provided")
    rusty_message = snapshot("""\
  × Expected an argument
   ╭────
 1 │ {{ foo|add }}
   ·        ─┬─
   ·         ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_add_safe(assert_render):
    template = "{{ html|safe|add:'<p>More HTML</p>' }}"
    html = "<p>Some HTML</p>"
    expected = "<p>Some HTML</p><p>More HTML</p>"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_add_integer_strings_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ foo|add:'3' }}{% endautoescape %}"
    assert_render(template=template, context={"foo": "2"}, expected="5")


def test_add_strings_autoescape_off(assert_render):
    template = "{% autoescape off %}{{ foo|add:'def' }}{% endautoescape %}"
    assert_render(template=template, context={"foo": "abc"}, expected="abcdef")


def test_add_bool(assert_render):
    template = "{% for x in 'abc' %}{{ forloop.first|add:forloop.last }}{% endfor %}"
    assert_render(template=template, context={}, expected="101")
