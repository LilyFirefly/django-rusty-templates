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
