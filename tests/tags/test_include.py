from django.template.exceptions import TemplateDoesNotExist


def test_include(assert_render):
    template = "{% for user in users %}{% include 'basic.txt' %}{% endfor %}"
    users = ["Lily", "Jacob", "Bryony"]
    expected = "Hello Lily!\nHello Jacob!\nHello Bryony!\n"
    assert_render(template=template, context={"users": users}, expected=expected)


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
