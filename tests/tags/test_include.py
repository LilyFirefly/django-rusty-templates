from pathlib import Path

import pytest
from django.template.base import VariableDoesNotExist
from django.template.exceptions import TemplateDoesNotExist, TemplateSyntaxError
from django.utils.translation import gettext_lazy


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


def test_include_with_extra_context(assert_render):
    template = "{% include 'name_snippet.txt' with person='Lily' greeting='Hello' %}{{ person }}"
    context = {"person": "Jacob"}
    expected = "Hello, Lily!\nJacob"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_extra_context_only(assert_render):
    template = "{% include 'name_snippet.txt' with greeting='Hi' only %}"
    context = {"person": "Jacob"}
    expected = "Hi, friend!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_empty_extra_context_only(assert_render):
    template = "{% include 'name_snippet.txt' only %}"
    context = {"person": "Jacob"}
    expected = ", friend!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_extra_context_only_kwarg(assert_render):
    template = "{% include 'name_snippet.txt' with greeting='Hi' only='only' %}"
    context = {"person": "Jacob"}
    expected = "Hi, Jacob!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_extra_context_only_before_with(assert_render):
    template = "{% include 'name_snippet.txt' only with greeting='Hi' %}"
    context = {"person": "Jacob"}
    expected = "Hi, friend!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_variable(assert_render):
    template = "{% include 'name_snippet.txt' with person=person greeting=greeting %}"
    context = {"greeting": "Hi"}
    expected = "Hi, friend!\n"
    assert_render(template=template, context=context, expected=expected)


def test_include_with_variable_only(assert_render):
    template = (
        "{% include 'name_snippet.txt' with person=person greeting=greeting only %}"
    )
    context = {"greeting": "Hi"}
    expected = "Hi, friend!\n"
    assert_render(template=template, context=context, expected=expected)


def test_relative(template_engine):
    template = template_engine.get_template("nested/relative.txt")
    assert template.render({}) == "Adjacent\n\nParent\n\n"


def test_relative_from_context(template_engine):
    template = template_engine.get_template("nested/relative.txt")
    context = {"adjacent": "./adjacent.txt", "parent": "../parent.txt"}
    assert template.render(context) == "Adjacent\n\nParent\n\n"


def test_relative_top_level(template_engine):
    template = template_engine.get_template("outside_hierarchy.txt")
    context = {"path": "./basic.txt", "user": "Lily"}
    assert template.render(context) == "Hello Lily!\n\n"


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


def test_incomplete_template_name(assert_parse_error):
    template = "{% include 'basic.txt %}"
    django_message = "Could not parse the remainder: ''basic.txt' from ''basic.txt'"
    rusty_message = """\
  × Expected a complete string literal
   ╭────
 1 │ {% include 'basic.txt %}
   ·            ─────┬────
   ·                 ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_template_name(assert_parse_error):
    template = "{% include basic-template %}"
    django_message = "Could not parse the remainder: '-template' from 'basic-template'"
    rusty_message = """\
  × Expected a valid variable name
   ╭────
 1 │ {% include basic-template %}
   ·            ───────┬──────
   ·                   ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_with(assert_parse_error):
    template = "{% include 'basic.txt' user='Lily' %}"
    django_message = "Unknown argument for 'include' tag: \"user='Lily'\"."
    rusty_message = """\
  × Unexpected argument
   ╭────
 1 │ {% include 'basic.txt' user='Lily' %}
   ·                        ─────┬─────
   ·                             ╰── here
   ╰────
  help: Try adding the 'with' keyword before the argument.
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_with_positional_variable(assert_parse_error):
    template = "{% include 'basic.txt' user %}"
    django_message = "Unknown argument for 'include' tag: 'user'."
    rusty_message = """\
  × Unexpected argument
   ╭────
 1 │ {% include 'basic.txt' user %}
   ·                        ──┬─
   ·                          ╰── here
   ╰────
  help: Try adding the 'with' keyword before the argument.
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_missing_with_positional_string(assert_parse_error):
    template = "{% include 'basic.txt' 'Lily' %}"
    django_message = "Unknown argument for 'include' tag: \"'Lily'\"."
    rusty_message = """\
  × Unexpected argument
   ╭────
 1 │ {% include 'basic.txt' 'Lily' %}
   ·                        ───┬──
   ·                           ╰── here
   ╰────
  help: Try adding the 'with' keyword before the argument.
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_missing_kwarg(assert_parse_error):
    template = "{% include 'basic.txt' with %}"
    django_message = "\"with\" in 'include' tag needs at least one keyword argument."
    rusty_message = """\
  × Expected a keyword argument
   ╭────
 1 │ {% include 'basic.txt' with %}
   ·                        ──┬─
   ·                          ╰── after this
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_only(assert_parse_error):
    template = "{% include 'basic.txt' with only %}"
    django_message = "\"with\" in 'include' tag needs at least one keyword argument."
    rusty_message = """\
  × Expected a keyword argument
   ╭────
 1 │ {% include 'basic.txt' with only %}
   ·                        ──┬─
   ·                          ╰── after this
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_only_only(assert_parse_error):
    template = "{% include 'basic.txt' only only %}"
    django_message = "The 'only' option was specified more than once."
    rusty_message = """\
  × The 'only' option was specified more than once.
   ╭────
 1 │ {% include 'basic.txt' only only %}
   ·                        ──┬─ ──┬─
   ·                          │    ╰── second here
   ·                          ╰── first here
   ╰────
  help: Remove the second 'only'
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_only_with_only(assert_parse_error):
    template = "{% include 'basic.txt' only with name='Lily' only %}"
    django_message = "The 'only' option was specified more than once."
    rusty_message = """\
  × The 'only' option was specified more than once.
   ╭────
 1 │ {% include 'basic.txt' only with name='Lily' only %}
   ·                        ──┬─                  ──┬─
   ·                          │                     ╰── second here
   ·                          ╰── first here
   ╰────
  help: Remove the second 'only'
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_syntax_after_only(assert_parse_error):
    template = "{% include 'basic.txt' with name='Lily' only 'partial %}"
    django_message = "Unknown argument for 'include' tag: \"'partial\"."
    rusty_message = """\
  × Expected a complete string literal
   ╭────
 1 │ {% include 'basic.txt' with name='Lily' only 'partial %}
   ·                                              ────┬───
   ·                                                  ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_syntax_with_or_only(assert_parse_error):
    template = "{% include 'basic.txt' 'partial %}"
    django_message = "Unknown argument for 'include' tag: \"'partial\"."
    rusty_message = """\
  × Expected a complete string literal
   ╭────
 1 │ {% include 'basic.txt' 'partial %}
   ·                        ────┬───
   ·                            ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_invalid_syntax_with_or_only_after_only(assert_parse_error):
    template = "{% include 'basic.txt' only 'partial %}"
    django_message = "Unknown argument for 'include' tag: \"'partial\"."
    rusty_message = """\
  × Expected a complete string literal
   ╭────
 1 │ {% include 'basic.txt' only 'partial %}
   ·                             ────┬───
   ·                                 ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_kwarg_after_only(assert_parse_error):
    template = "{% include 'name_snippet.txt' with person='Lily' only greeting='Hi' %}"
    django_message = "Unknown argument for 'include' tag: \"greeting='Hi'\"."
    rusty_message = """\
  × Unexpected argument
   ╭────
 1 │ {% include 'name_snippet.txt' with person='Lily' only greeting='Hi' %}
   ·                                                       ──────┬──────
   ·                                                             ╰── here
   ╰────
  help: Try moving the argument before the 'only' option
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_positional_arg(assert_parse_error):
    template = "{% include 'basic.txt' with user %}"
    django_message = "\"with\" in 'include' tag needs at least one keyword argument."
    rusty_message = """\
  × Expected a keyword argument
   ╭────
 1 │ {% include 'basic.txt' with user %}
   ·                             ──┬─
   ·                               ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_positional_arg_after_kwarg(assert_parse_error):
    template = "{% include 'name_snippet.txt' with person='Lily' greeting %}"
    django_message = "Unknown argument for 'include' tag: 'greeting'."
    rusty_message = """\
  × Expected a keyword argument
   ╭────
 1 │ {% include 'name_snippet.txt' with person='Lily' greeting %}
   ·                                                  ────┬───
   ·                                                      ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_broken_keyword_argument(assert_parse_error):
    template = "{% include 'name_snippet.txt' with person='Lily %}"
    django_message = "Could not parse the remainder: ''Lily' from ''Lily'"
    rusty_message = """\
  × Expected a complete string literal
   ╭────
 1 │ {% include 'name_snippet.txt' with person='Lily %}
   ·                                           ──┬──
   ·                                             ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_with_invalid_keyword_argument(assert_parse_error):
    template = "{% include 'name_snippet.txt' with person=basic-template %}"
    django_message = "Could not parse the remainder: '-template' from 'basic-template'"
    rusty_message = """\
  × Expected a valid variable name
   ╭────
 1 │ {% include 'name_snippet.txt' with person=basic-template %}
   ·                                           ───────┬──────
   ·                                                  ╰── here
   ╰────
"""
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_relative_from_string_template(assert_parse_error):
    template = "{% include './adjacent.txt' %}"
    django_message = "'NoneType' object has no attribute 'lstrip'"
    rusty_message = """\
  × The relative path './adjacent.txt' cannot be evaluated due to an unknown
  │ template origin.
   ╭────
 1 │ {% include './adjacent.txt' %}
   ·             ───────┬──────
   ·                    ╰── here
   ╰────
"""
    assert_parse_error(
        template=template,
        django_message=django_message,
        rusty_message=rusty_message,
        exception=AttributeError,
        rusty_exception=TemplateSyntaxError,
    )


def test_relative_from_string_template_variable(assert_render_error):
    template = "{% include path %}"
    path = "./adjacent.txt"
    django_message = "'NoneType' object has no attribute 'lstrip'"
    rusty_message = """\
  × The relative path './adjacent.txt' cannot be evaluated due to an unknown
  │ template origin.
   ╭────
 1 │ {% include path %}
   ·            ──┬─
   ·              ╰── here
   ╰────
"""
    assert_render_error(
        template=template,
        context={"path": path},
        django_message=django_message,
        rusty_message=rusty_message,
        exception=AttributeError,
        rusty_exception=TemplateSyntaxError,
    )


def test_relative_outside_file_hierarchy(template_engine):
    template = "nested/outside_hierarchy.txt"
    absolute_template = (Path("tests/templates") / template).absolute()

    with pytest.raises(TemplateSyntaxError) as exc_info:
        template_engine.get_template(template)

    django_message = f"The relative path ''../../outside.txt'' points outside the file hierarchy that template '{template}' is in."
    rusty_message = (
        """\
  × The relative path '../../outside.txt' points outside the file hierarchy
  │ that template 'nested/outside_hierarchy.txt' is in.
   ╭─[%s:1:13]
 1 │ {%% include '../../outside.txt' %%}
   ·             ────────┬────────
   ·                     ╰── relative path
   ╰────
"""
        % absolute_template
    )

    if template_engine.name == "django":
        assert str(exc_info.value) == django_message
    else:
        assert str(exc_info.value) == rusty_message


def test_relative_outside_file_hierarchy_variable(template_engine):
    template_path = "nested/outside_hierarchy2.txt"
    relative_path = "../../outside.txt"

    template = template_engine.get_template(template_path)
    with pytest.raises(TemplateSyntaxError) as exc_info:
        template.render({"path": relative_path})

    django_message = f"The relative path '{relative_path}' points outside the file hierarchy that template '{template_path}' is in."
    rusty_message = """\
  × The relative path '../../outside.txt' points outside the file hierarchy
  │ that template 'nested/outside_hierarchy2.txt' is in.
   ╭────
 1 │ {% include path %}
   ·            ──┬─
   ·              ╰── relative path
   ╰────
"""

    if template_engine.name == "django":
        assert str(exc_info.value) == django_message
    else:
        assert str(exc_info.value) == rusty_message


def test_relative_outside_top_level(template_engine):
    template_path = "outside_hierarchy.txt"
    relative_path = "../outside.txt"

    template = template_engine.get_template(template_path)
    with pytest.raises(TemplateSyntaxError) as exc_info:
        template.render({"path": relative_path})

    django_message = f"The relative path '{relative_path}' points outside the file hierarchy that template '{template_path}' is in."
    rusty_message = """\
  × The relative path '../outside.txt' points outside the file hierarchy that
  │ template 'outside_hierarchy.txt' is in.
   ╭────
 1 │ {% include path %}
   ·            ──┬─
   ·              ╰── relative path
   ╰────
"""

    if template_engine.name == "django":
        assert str(exc_info.value) == django_message
    else:
        assert str(exc_info.value) == rusty_message


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


def test_include_missing_attribute(assert_render_error):
    template = "{% include value.missing %}"
    django_message = "No template names provided"
    rusty_message = """\
  × Failed lookup for key [missing] in {}
   ╭────
 1 │ {% include value.missing %}
   ·            ──┬── ───┬───
   ·              │      ╰── key
   ·              ╰── {}
   ╰────
"""
    assert_render_error(
        template=template,
        context={"value": {}},
        exception=TemplateDoesNotExist,
        rusty_exception=VariableDoesNotExist,
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


def test_include_missing_template_string(assert_render_error):
    template = "{% include 'missing.txt' %}"
    django_message = "missing.txt"
    rusty_message = """\
  × missing.txt
   ╭────
 1 │ {% include 'missing.txt' %}
   ·             ─────┬─────
   ·                  ╰── here
   ╰────
"""
    assert_render_error(
        template=template,
        context={},
        exception=TemplateDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_missing_template_variable(assert_render_error):
    template = "{% include missing %}"
    django_message = "missing.txt"
    rusty_message = """\
  × missing.txt
   ╭────
 1 │ {% include missing %}
   ·            ───┬───
   ·               ╰── here
   ╰────
"""
    assert_render_error(
        template=template,
        context={"missing": "missing.txt"},
        exception=TemplateDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_missing_template_variable_list(assert_render_error):
    template = "{% include missing %}"
    django_message = "missing.txt, missing2.txt"
    rusty_message = """\
  × missing.txt, missing2.txt
   ╭────
 1 │ {% include missing %}
   ·            ───┬───
   ·               ╰── here
   ╰────
"""
    assert_render_error(
        template=template,
        context={"missing": ["missing.txt", "missing2.txt"]},
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


def test_include_integer_filter(assert_render_error):
    template = "{% include numeric|add:3 %}"
    django_message = "'int' object is not iterable"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% include numeric|add:3 %}
   ·            ─────┬─────
   ·                 ╰── invalid template name: 5
   ╰────
"""
    assert_render_error(
        template=template,
        context={"numeric": 2},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_float_filter(assert_render_error):
    template = "{% include missing|default:3.2 %}"
    django_message = "'float' object is not iterable"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% include missing|default:3.2 %}
   ·            ───────┬───────
   ·                   ╰── invalid template name: 3.2
   ╰────
"""
    assert_render_error(
        template=template,
        context={},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_bool_filter_true(assert_render_error):
    template = "{% for a in b %}{% include forloop.first %}{% endfor %}"
    django_message = "'bool' object is not iterable"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% for a in b %}{% include forloop.first %}{% endfor %}
   ·                            ──────┬──────
   ·                                  ╰── invalid template name: True
   ╰────
"""
    assert_render_error(
        template=template,
        context={"b": ["a"]},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_missing_relative_template(assert_render_error):
    template = "{% include 'nested/invalid.txt' %}"
    django_message = "nested/missing.txt"
    rusty_message = """\
  × nested/missing.txt
   ╭────
 1 │ {% include "./missing.txt" %}
   ·             ──────┬──────
   ·                   ╰── here
   ╰────
"""
    assert_render_error(
        template=template,
        context={},
        exception=TemplateDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_include_bool_filter_false(template_engine):
    template = "{% for a in b %}{% include forloop.last %}{% endfor %}"
    django_message = "No template names provided"
    rusty_message = """\
  × Included template name must be a string or iterable of strings.
   ╭────
 1 │ {% for a in b %}{% include forloop.last %}{% endfor %}
   ·                            ──────┬─────
   ·                                  ╰── invalid template name: False
   ╰────
"""
    template = template_engine.from_string(template)

    if template_engine.name == "django":
        with pytest.raises(TemplateDoesNotExist) as exc_info:
            template.render({"b": ["a", "b"]})

        assert str(exc_info.value) == django_message

    else:
        with pytest.raises(TypeError) as exc_info:
            template.render({"b": ["a", "b"]})

        assert str(exc_info.value) == rusty_message


def test_include_translated(template_engine):
    template = "{% include _('basic.txt') %}"
    rusty_message = """\
  × Included template name cannot be a translatable string.
   ╭────
 1 │ {% include _('basic.txt') %}
   ·            ───────┬──────
   ·                   ╰── invalid template name
   ╰────
"""

    if template_engine.name == "rusty":
        with pytest.raises(TemplateSyntaxError) as exc_info:
            template_engine.from_string(template)

        assert str(exc_info.value) == rusty_message

    else:
        template = template_engine.from_string(template)

        # IsADirectoryError on Unix
        # PermissionError on Windows
        with pytest.raises((IsADirectoryError, PermissionError)):
            template.render({})


def test_include_translated_variable(template_engine):
    template = "{% include translated %}"
    rusty_message = """\
  × Included template name cannot be a translatable string.
   ╭────
 1 │ {% include translated %}
   ·            ─────┬────
   ·                 ╰── invalid template name: 'basic.txt'
   ╰────
"""

    context = {"translated": gettext_lazy("basic.txt")}
    template = template_engine.from_string(template)

    if template_engine.name == "rusty":
        with pytest.raises(TypeError) as exc_info:
            template.render(context)

        assert str(exc_info.value) == rusty_message

    else:
        # IsADirectoryError on Unix
        # PermissionError on Windows
        with pytest.raises((IsADirectoryError, PermissionError)):
            template.render(context)
