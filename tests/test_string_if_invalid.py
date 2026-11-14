from .conftest import locmem_config


def test_invalid_variable(engine_class):
    string_if_invalid = "INVALID"
    template_string = "{{ missing }}"
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = string_if_invalid
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context={}) == string_if_invalid
