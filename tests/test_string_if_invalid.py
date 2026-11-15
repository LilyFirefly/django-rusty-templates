import pytest
from django.template.backends.django import DjangoTemplates
from inline_snapshot import snapshot

from .conftest import locmem_config


def test_invalid_variable(engine_class):
    template_string = "{{ missing }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALID"


def test_invalid_variable_in_default_filter(engine_class):
    template_string = "{{ missing|default:'valid' }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALID"


def test_invalid_variable_in_default_if_none_filter(engine_class):
    template_string = "{{ missing|default_if_none:'valid' }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALID"


def test_invalid_variable_in_block_super(engine_class):
    parent = "{% block b %}{{ missing }}{% endblock %}"
    child = "{% extends 'parent' %}{% block b %}{{ block.super }}{% endblock %}"
    config = locmem_config({"parent": parent}, {"child": child})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("child")

    assert template.render(context={}) == "INVALID"


def test_invalid_variable_in_simple_tag(engine_class):
    template_string = "{% load double from custom_tags %}{% double missing %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALIDINVALID"


def test_invalid_variable_in_simple_tag_kwargs(engine_class):
    template_string = (
        "{% load combine from custom_tags %}{% combine 1 2 operation=operation %}"
    )
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "add"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "3"


def test_invalid_variable_in_simple_block_tag(engine_class):
    template_string = "{% load repeat_prefix from custom_tags %}{% repeat_prefix 2 missing %}inner{% endrepeat_prefix %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALIDinnerINVALIDinner"


def test_invalid_variable_in_cycle(engine_class):
    template_string = "{% for item in items %}{% cycle missing 'b' %}{% endfor %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={"items": range(2)}) == "INVALIDb"


def test_invalid_variable_in_named_cycle(engine_class):
    template_string = "{% cycle missing 'b' as c %}{% cycle c %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "INVALIDb"


def test_invalid_variable_in_silent_named_cycle(engine_class):
    template_string = (
        "{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}"
    )
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={"items": range(2)}) == "INVALIDb"


def test_invalid_addition_in_add_filter_with_string_if_invalid(engine_class):
    template_string = "{{ number|add:'string' }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={"number": 2}) == ""


def test_url_tag_as_var_with_string_if_invalid(engine_class):
    template_string = "{% url 'home' as home %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == ""


def test_url_tag_missing_view_as_var_with_string_if_invalid(engine_class):
    template_string = "{% url 'missing' as missing %}{{ missing }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == ""


def test_invalid_variable_formatted(engine_class):
    template_string = "{{ missing }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missing"


def test_invalid_variable_in_default_filter_formatted(engine_class):
    template_string = "{{ missing|default:'valid' }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missing"


def test_invalid_variable_in_default_if_none_filter_formatted(engine_class):
    template_string = "{{ missing|default_if_none:'valid' }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missing"


def test_invalid_variable_in_block_super_formatted(engine_class):
    parent = "{% block b %}{{ missing }}{% endblock %}"
    child = "{% extends 'parent' %}{% block b %}{{ block.super }}{% endblock %}"
    config = locmem_config({"parent": parent}, {"child": child})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("child")

    assert template.render(context={}) == "missing"


def test_invalid_variable_in_simple_tag_formatted(engine_class):
    template_string = "{% load double from custom_tags %}{% double missing %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missingmissing"


def test_invalid_variable_in_simple_tag_kwargs_formatted(engine_class, request):
    template_string = (
        "{% load combine from custom_tags %}{% combine 1 2 operation=operation %}"
    )
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    with pytest.raises(RuntimeError) as exc_info:
        template.render(context={})

    message = str(exc_info.value)
    if engine_class is DjangoTemplates:
        assert message == snapshot("Unknown operation")
    else:
        assert message == snapshot("""\
  × Unknown operation
   ╭────
 1 │ {% load combine from custom_tags %}{% combine 1 2 operation=operation %}
   ·                                    ──────────────────┬──────────────────
   ·                                                      ╰── here
   ╰────
""")


def test_invalid_variable_in_simple_block_tag_formatted(engine_class):
    template_string = "{% load repeat_prefix from custom_tags %}{% repeat_prefix 2 missing %}inner{% endrepeat_prefix %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missinginnermissinginner"


def test_invalid_variable_in_cycle_formatted(engine_class):
    template_string = "{% for item in items %}{% cycle missing 'b' %}{% endfor %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={"items": range(2)}) == "missingb"


def test_invalid_variable_in_named_cycle_formatted(engine_class):
    template_string = "{% cycle missing 'b' as c %}{% cycle c %}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == "missingb"


def test_invalid_variable_in_silent_named_cycle_formatted(engine_class):
    template_string = (
        "{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}"
    )
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={"items": range(2)}) == "missingb"
