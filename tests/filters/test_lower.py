from django.template import engines


def test_lower_integer():
    template = "{{ foo|default:3|lower }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "3"
    assert rust_template.render({}) == "3"


def test_lower_float():
    template = "{{ foo|default:3.7|lower }}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "3.7"
    assert rust_template.render({}) == "3.7"


def test_lower_bool():
    template = "{% for x in 'ab' %}{{ forloop.first|lower }}{% endfor %}"
    django_template = engines["django"].from_string(template)
    rust_template = engines["rusty"].from_string(template)

    assert django_template.render({}) == "truefalse"
    assert rust_template.render({}) == "truefalse"
