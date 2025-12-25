from inline_snapshot import snapshot
from django.template.base import VariableDoesNotExist


def test_load_and_render_filters(assert_render):
    template = "{% load custom_filters %}{{ text|cut:'ello' }}"
    text = "Hello World!"
    expected = "H World!"
    assert_render(template=template, context={"text": text}, expected=expected)


def test_load_and_render_single_filter(assert_render):
    template = "{% load cut from custom_filters %}{{ text|cut:'ello' }}"
    text = "Hello World!"
    expected = "H World!"
    assert_render(template=template, context={"text": text}, expected=expected)


def test_load_and_render_multiple_filters(assert_render):
    template = """{% load cut double multiply from custom_filters %}
{{ text|cut:'ello' }}
{{ num|double }}
{{ num|multiply }}
{{ num|multiply:4 }}
"""
    text = "Hello World!"
    expected = "\nH World!\n4\n6\n8\n"
    assert_render(
        template=template, context={"text": text, "num": 2}, expected=expected
    )


def test_load_and_render_multiple_filter_libraries(assert_render):
    template = "{% load custom_filters more_filters %}{{ num|double|square }}"
    assert_render(template=template, context={"num": 2}, expected="16")


def test_resolve_filter_arg_error(assert_render_error):
    django_message = snapshot("Failed lookup for key [1b] in 3")
    rusty_message = snapshot("""\
  × Failed lookup for key [1b] in 3
   ╭─[2:17]
 1 │ {% load multiply from custom_filters %}
 2 │ {{ num|multiply:foo.bar.1b.baz }}
   ·                 ───┬─── ─┬
   ·                    │     ╰── key
   ·                    ╰── 3
   ╰────
""")
    template = """\
{% load multiply from custom_filters %}
{{ num|multiply:foo.bar.1b.baz }}
"""
    assert_render_error(
        template=template,
        context={"num": 2, "foo": {"bar": 3}},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_filter_error(assert_render_error):
    assert_render_error(
        template="{% load custom_filters %}{{ num|divide_by_zero }}",
        context={"num": 1},
        exception=ZeroDivisionError,
        django_message=snapshot("division by zero"),
        rusty_message=snapshot("division by zero"),
    )


def test_filter_error_with_argument(assert_render_error):
    assert_render_error(
        template="{% load custom_filters %}{{ num|divide_by_zero:0 }}",
        context={"num": 1},
        exception=ZeroDivisionError,
        django_message=snapshot("division by zero"),
        rusty_message=snapshot("division by zero"),
    )
