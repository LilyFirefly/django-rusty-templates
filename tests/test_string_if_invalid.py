from .conftest import locmem_config


def test_invalid_variable(engine_class):
    template_string = "{{ missing }}"
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
