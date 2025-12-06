import pytest
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError


def test_include(assert_render):
    template = "{% for user in users %}{% include 'basic.txt' %}{% endfor %}"
    users = ["Lily", "Jacob", "Bryony"]
    expected = "Hello Lily!\nHello Jacob!\nHello Bryony!\n"
    assert_render(template=template, context={"users": users}, expected=expected)


def test_include_variable(assert_render):
    template = "{% include template %}"
    context = {"user": "Lily", "template": "basic.txt"}
    expected = "Hello Lily!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_list(assert_render):
    template = "{% include templates %}"
    context = {"user": "Lily", "templates": ["missing.txt", "basic.txt"]}
    expected = "Hello Lily!\n"
    assert_render(template=template, context=context, expected=expected)


def test_empty_include(assert_parse_error):
    template = "{% include %}"
    django_message = "'include' tag takes at least one argument: the name of the template to be included."
    rusty_message = """\
  × Expected an argument
   ╭────
 1 │ {% include %}
   · ──────┬──────
   ·       ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_template_name_keyword(assert_parse_error):
    template = "{% include template_name='basic.txt' %}"
    django_message = (
        "Could not parse the remainder: '='basic.txt'' from 'template_name='basic.txt''"
    )
    rusty_message = """\
  × Unexpected keyword argument
   ╭────
 1 │ {% include template_name='basic.txt' %}
   ·            ──────┬──────
   ·                  ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_include_missing_variable(assert_render_error):
    template = "{% include missing %}"
    django_message = "No template names provided"
    rusty_message = """\
  × No template names provided
   ╭────
 1 │ {% include missing %}
   ·            ───┬───
   ·               ╰── This variable is not in the context
   ╰────
"""
    assert_render_error(
        template=template,
        context={},
        exception=TemplateDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_missing_filter_variable(assert_render_error):
    template = "{% include missing|add:3 %}"
    django_message = "No template names provided"
    rusty_message = """\
  × No template names provided
   ╭────
 1 │ {% include missing|add:3 %}
   ·            ─────┬─────
   ·                 ╰── This variable is not in the context
   ╰────
"""
    assert_render_error(
        template=template,
        context={},
        exception=TemplateDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_numeric(template_engine):
    template = "{% include 1 %}"
    django_message = "'int' object is not iterable"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% include 1 %}
   ·            ┬
   ·            ╰── invalid template name
   ╰────
"""

    if template_engine.name == "rusty":
        with pytest.raises(TemplateSyntaxError) as exc_info:
            template_engine.from_string(template)

        assert str(exc_info.value) == rusty_message

    else:
        template = template_engine.from_string(template)

        with pytest.raises(TypeError) as exc_info:
            template.render({})

        assert str(exc_info.value) == django_message


def test_include_numeric_variable(assert_render_error):
    template = "{% include numeric %}"
    django_message = "'int' object is not iterable"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% include numeric %}
   ·            ───┬───
   ·               ╰── invalid template name: 1
   ╰────
"""
    assert_render_error(
        template=template,
        context={"numeric": 1},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )
