import pytest
from django.template.backends.django import DjangoTemplates
from inline_snapshot import snapshot

from .conftest import locmem_config


@pytest.mark.parametrize(
    "template_string,invalid,expected,context",
    (
        ("{{ missing }}", "INVALID", "INVALID", {}),
        ("{{ missing }}", "%s", "missing", {}),
        ("{{ missing }}", "<b>%s</b>", "&lt;b&gt;missing&lt;/b&gt;", {}),
        (
            "{% autoescape off %}{{ missing }}{% endautoescape %}",
            "<b>%s</b>",
            "<b>missing</b>",
            {},
        ),
        ("{{ missing|capfirst }}", "invalid", "invalid", {}),
        ("{{ missing|capfirst }}", "%s", "missing", {}),
        (
            "{% autoescape off %}{{ missing|escape }}{% endautoescape %}",
            "<invalid>",
            "<invalid>",
            {},
        ),
        ("{{ missing|escape }}", "%s", "missing", {}),
        (
            "{% autoescape off %}{{ missing|escapejs }}{% endautoescape %}",
            "{'invalid': 'invalid'}",
            "{'invalid': 'invalid'}",
            {},
        ),
        ("{{ missing|escapejs }}", "%s", "missing", {}),
        ("{{ missing|length }}", "INVALID", "INVALID", {}),
        ("{{ missing|length }}", "%s", "missing", {}),
        ("{{ missing|lower }}", "INVALID", "INVALID", {}),
        ("{{ missing|lower }}", "%s", "missing", {}),
        ("{{ missing|upper }}", "invalid", "invalid", {}),
        ("{{ missing|upper }}", "%s", "missing", {}),
        ("{{ missing|safe }}", "INVALID", "INVALID", {}),
        ("{{ missing|safe }}", "%s", "missing", {}),
        ("{{ missing|slugify }}", "INVALID", "INVALID", {}),
        ("{{ missing|slugify }}", "%s", "missing", {}),
        ("{{ missing|wordcount }}", "INVALID", "INVALID", {}),
        ("{{ missing|wordcount }}", "%s", "missing", {}),
        ("{{ missing|yesno }}", "INVALID", "INVALID", {}),
        ("{{ missing|yesno }}", "%s", "missing", {}),
        (
            "{% autoescape off %}{{ missing|addslashes }}{% endautoescape %}",
            "inv'alid",
            "inv'alid",
            {},
        ),
        ("{{ missing|addslashes }}", "%s", "missing", {}),
        ("{{ missing|default:'valid' }}", "INVALID", "INVALID", {}),
        ("{{ missing|default:'valid' }}", "%s", "missing", {}),
        ("{{ missing|default_if_none:'valid' }}", "INVALID", "INVALID", {}),
        ("{{ missing|default_if_none:'valid' }}", "%s", "missing", {}),
        (
            "{% if missing|default:missing2 %}yes{% else %}no{% endif %}",
            "INVALID",
            "no",
            {},
        ),
        (
            "{% if missing|default:'exists' %}yes{% else %}no{% endif %}",
            "INVALID",
            "yes",
            {},
        ),
        (
            "{% if missing|default_if_none:missing2 %}yes{% else %}no{% endif %}",
            "INVALID",
            "no",
            {},
        ),
        (
            "{% if missing|default_if_none:exists %}yes{% else %}no{% endif %}",
            "INVALID",
            "yes",
            {"exists": 1},
        ),
        (
            "{% load double from custom_tags %}{% double missing %}",
            "INVALID",
            "INVALIDINVALID",
            {},
        ),
        (
            "{% load double from custom_tags %}{% double missing %}",
            "%s",
            "missingmissing",
            {},
        ),
        (
            "{% load combine from custom_tags %}{% combine 1 2 operation=operation %}",
            "add",
            "3",
            {},
        ),
        (
            "{% load repeat_prefix from custom_tags %}{% repeat_prefix 2 missing %}inner{% endrepeat_prefix %}",
            "INVALID",
            "INVALIDinnerINVALIDinner",
            {},
        ),
        (
            "{% load repeat_prefix from custom_tags %}{% repeat_prefix 2 missing %}inner{% endrepeat_prefix %}",
            "%s",
            "missinginnermissinginner",
            {},
        ),
        (
            "{% for item in items %}{% cycle missing 'b' %}{% endfor %}",
            "INVALID",
            "INVALIDb",
            {"items": range(2)},
        ),
        (
            "{% for item in items %}{% cycle missing 'b' %}{% endfor %}",
            "%s",
            "missingb",
            {"items": range(2)},
        ),
        (
            "{% for item in items %}{% cycle missing 'b' %}{% endfor %}",
            "<b>%s</b>",
            "&lt;b&gt;missing&lt;/b&gt;b",
            {"items": range(2)},
        ),
        (
            "{% autoescape off %}{% for item in items %}{% cycle missing 'b' %}{% endfor %}{% endautoescape %}",
            "<b>%s</b>",
            "<b>missing</b>b",
            {"items": range(2)},
        ),
        ("{% cycle missing 'b' as c %}{% cycle c %}", "INVALID", "INVALIDb", {}),
        ("{% cycle missing 'b' as c %}{% cycle c %}", "%s", "missingb", {}),
        (
            "{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}",
            "INVALID",
            "INVALIDb",
            {"items": range(2)},
        ),
        (
            "{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}",
            "%s",
            "missingb",
            {"items": range(2)},
        ),
        (
            "{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}",
            "<b>%s</b>",
            "&lt;b&gt;missing&lt;/b&gt;b",
            {"items": range(2)},
        ),
        (
            "{% autoescape off %}{% for item in items %}{% cycle missing 'b' as c silent %}{{ c }}{% endfor %}{% endautoescape %}",
            "<b>%s</b>",
            "<b>missing</b>b",
            {"items": range(2)},
        ),
        (
            "{% cycle missing 'b' as c %}{% cycle c %}",
            "<b>%s</b>",
            "&lt;b&gt;missing&lt;/b&gt;b",
            {},
        ),
        (
            "{% autoescape off %}{% cycle missing 'b' as c %}{% cycle c %}{% endautoescape %}",
            "<b>%s</b>",
            "<b>missing</b>b",
            {},
        ),
        (
            "{% cycle 'a' missing as c %}{% cycle c %}",
            "<b>%s</b>",
            "a&lt;b&gt;missing&lt;/b&gt;",
            {},
        ),
        (
            "{% autoescape off %}{% cycle 'a' missing as c %}{% cycle c %}{% endautoescape %}",
            "<b>%s</b>",
            "a<b>missing</b>",
            {},
        ),
        ("{{ number|add:'string' }}", "INVALID", "", {"number": 2}),
        ("{% url 'home' as home %}", "INVALID", "", {}),
        ("{% url 'missing' as missing %}{{ missing }}", "INVALID", "", {}),
    ),
)
def test_invalid_variable(engine_class, template_string, invalid, expected, context):
    config = locmem_config({"template": template_string})
    config["OPTIONS"]["string_if_invalid"] = invalid
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.render(context=context) == expected


def test_invalid_variable_in_block_super(engine_class):
    parent = "{% block b %}{{ missing }}{% endblock %}"
    child = "{% extends 'parent' %}{% block b %}{{ block.super }}{% endblock %}"
    config = locmem_config({"parent": parent}, {"child": child})
    config["OPTIONS"]["string_if_invalid"] = "INVALID"
    engine = engine_class(config)

    template = engine.get_template("child")

    assert template.render(context={}) == "INVALID"


def test_invalid_variable_in_block_super_formatted(engine_class):
    parent = "{% block b %}{{ missing }}{% endblock %}"
    child = "{% extends 'parent' %}{% block b %}{{ block.super }}{% endblock %}"
    config = locmem_config({"parent": parent}, {"child": child})
    config["OPTIONS"]["string_if_invalid"] = "%s"
    engine = engine_class(config)

    template = engine.get_template("child")

    assert template.render(context={}) == "missing"


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
