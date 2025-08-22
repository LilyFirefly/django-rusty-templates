import pytest
from django.template import engines
from django.template.exceptions import TemplateSyntaxError


def test_render_variable():
    template = "{{ foo }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": 3}) == "3"
    assert rust_template.render({"foo": 3}) == "3"


def test_render_int():
    template = "{{ 1 }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"1": 2}) == "1"
    assert rust_template.render({"1": 2}) == "1"


def test_render_float():
    template = "{{ 1.2 }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"1.2": 2}) == "1.2"
    assert rust_template.render({"1.2": 2}) == "1.2"


def test_render_negative_int():
    template = "{{ -1 }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"-1": 2}) == "-1"
    assert rust_template.render({"-1": 2}) == "-1"


def test_render_negative_float():
    template = "{{ -1.2 }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"-1.2": 2}) == "-1.2"
    assert rust_template.render({"-1.2": 2}) == "-1.2"


def test_render_attribute_int():
    template = "{{ foo.1 }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": {1: 3}}) == "3"
    assert rust_template.render({"foo": {1: 3}}) == "3"


def test_render_variable_hyphen():
    template = "{{ foo-1 }}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Could not parse the remainder: '-1' from 'foo-1'"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {{ foo-1 }}
   ·    ──┬──
   ·      ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_attribute_negative_int():
    template = "{{ foo.-1 }}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Could not parse the remainder: '-1' from 'foo.-1'"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {{ foo.-1 }}
   ·        ─┬
   ·         ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_invalid_variable():
    template = "{{ & }}"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["django"].from_string(template)

    assert str(exc_info.value) == "Could not parse the remainder: '&' from '&'"

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engines["rusty"].from_string(template)

    expected = """\
  × Expected a valid variable name
   ╭────
 1 │ {{ & }}
   ·    ┬
   ·    ╰── here
   ╰────
"""
    assert str(exc_info.value) == expected


def test_render_variable_callable():
    template = "{{ foo }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": lambda: 3}) == "3"
    assert rust_template.render({"foo": lambda: 3}) == "3"


def test_render_attribute_callable():
    template = "{{ foo.bar }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({"foo": {"bar": lambda: 3}}) == "3"
    assert rust_template.render({"foo": {"bar": lambda: 3}}) == "3"


class DoNotCall:
    do_not_call_in_templates = True
    attr = "attribute"

    def __call__(self):
        return "called"

    def __str__(self):
        return "not called"


class AltersData:
    def __init__(self):
        self.data = 0

    def increment(self):
        self.data += 1

    increment.alters_data = True


class Both:
    do_not_call_in_templates = True
    alters_data = True

    def __init__(self):
        self.data = 0

    def __call__(self):
        self.data += 1
        return "called"

    def __str__(self):
        return "not called"


def test_render_callable_do_not_call_in_templates():
    template = "{{ do_not_call }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"do_not_call": DoNotCall()}
    assert django_template.render(context) == "not called"
    assert rust_template.render(context) == "not called"


def test_render_callable_do_not_call_in_templates_attribute():
    template = "{{ do_not_call.attr }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    context = {"do_not_call": DoNotCall()}
    assert django_template.render(context) == "attribute"
    assert rust_template.render(context) == "attribute"


def test_render_callable_attribute_alters_data():
    template = "{{ foo.increment }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    mutable = AltersData()
    context = {"foo": mutable}
    assert django_template.render(context) == ""
    assert mutable.data == 0
    assert rust_template.render(context) == ""
    assert mutable.data == 0


def test_render_callable_variable_alters_data():
    template = "{{ increment }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    mutable = AltersData()
    context = {"increment": mutable.increment}
    assert django_template.render(context) == ""
    assert mutable.data == 0
    assert rust_template.render(context) == ""
    assert mutable.data == 0


def test_do_not_call_and_alters_data():
    template = "{{ foo.data }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    both = Both()
    context = {"foo": both}
    assert django_template.render(context) == "0"
    assert both.data == 0
    assert rust_template.render(context) == "0"
    assert both.data == 0
