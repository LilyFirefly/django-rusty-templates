import pytest
from django.template import TemplateSyntaxError
from django.utils.translation import gettext_lazy
from inline_snapshot import snapshot


def test_blocks(assert_render):
    template = """
{% block header %}# {{ title }}{% endblock header %}
{% block body %}Hello {{ user.name }}!{% endblock %}
"""
    assert_render(
        template=template,
        context={"title": "Using blocks", "user": {"name": "Lily"}},
        expected="\n# Using blocks\nHello Lily!\n",
    )


def test_extends_no_blocks(assert_render):
    template = "{% extends 'basic.txt' %}"
    assert_render(template=template, context={"user": "Lily"}, expected="Hello Lily!\n")


def test_extends(assert_render):
    template = "{% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    assert_render(template=template, context={}, expected="# Header\nSome content\n")


def test_extends_variable(assert_render):
    template = (
        "{% extends template_name %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(
        template=template,
        context={"template_name": "base.txt"},
        expected="# Header\nSome content\n",
    )


def test_extends_variable_lazy_translation(assert_render):
    template = (
        "{% extends template_name %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(
        template=template,
        context={"template_name": gettext_lazy("base.txt")},
        expected="# Header\nSome content\n",
    )


def test_extends_translation(assert_render, template_engine):
    if template_engine.name == "rusty":
        pytest.xfail("Support for translation is not implemented yet")

    template = (
        "{% extends _('base.txt') %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(
        template=template,
        context={"template_name": gettext_lazy("base.txt")},
        expected="# Header\nSome content\n",
    )


def test_extends_endblock_no_name(assert_render):
    template = "{% extends 'base.txt' %}{% block body %}Some content{% endblock %}"
    assert_render(template=template, context={}, expected="# Header\nSome content\n")


def test_extends_super(assert_render):
    template = """\
{% extends 'base.txt' %}{% block header %}{{ block.super }}
## Subtitle{% endblock header %}{% block body %}Some content{% endblock body %}"""
    assert_render(
        template=template, context={}, expected="# Header\n## Subtitle\nSome content\n"
    )


def test_extends_after_whitespace(assert_render):
    template = (
        "  {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(template=template, context={}, expected="  # Header\nSome content\n")


def test_extends_after_text(assert_render):
    template = (
        "Text {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(
        template=template, context={}, expected="Text # Header\nSome content\n"
    )


def test_extends_after_comment(assert_render):
    template = "{# Comment #}{% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    assert_render(template=template, context={}, expected="# Header\nSome content\n")


def test_extends_after_variable(assert_parse_error):
    template = "{{ variable }} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    django_message = snapshot(
        "{% extends 'base.txt' %} must be the first tag in the template."
    )
    rusty_message = snapshot("""\
  × {% extends 'base.txt' %} must be the first tag in the template.
   ╭────
 1 │ {{ variable }} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}
   · ───────┬────── ────────────┬───────────
   ·        │                   ╰── extends tag here
   ·        ╰── first tag here
   ╰────
  help: Move the extends tag before other tags and variables.
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_after_tag(assert_parse_error):
    template = "{% url 'home' %} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    django_message = snapshot(
        "{% extends 'base.txt' %} must be the first tag in the template."
    )
    rusty_message = snapshot("""\
  × {% extends 'base.txt' %} must be the first tag in the template.
   ╭────
 1 │ {% url 'home' %} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}
   · ────────┬─────── ────────────┬───────────
   ·         │                    ╰── extends tag here
   ·         ╰── first tag here
   ╰────
  help: Move the extends tag before other tags and variables.
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_after_load_tag(assert_parse_error):
    template = "{% load custom_tags %} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    django_message = snapshot(
        "{% extends 'base.txt' %} must be the first tag in the template."
    )
    rusty_message = snapshot("""\
  × {% extends 'base.txt' %} must be the first tag in the template.
   ╭────
 1 │ {% load custom_tags %} {% extends 'base.txt' %}{% block body %}Some content{% endblock body %}
   · ───────────┬────────── ────────────┬───────────
   ·            │                       ╰── extends tag here
   ·            ╰── first tag here
   ╰────
  help: Move the extends tag before other tags and variables.
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_block_too_many_arguments(assert_parse_error):
    template = "{% extends 'base.txt' %}{% block body with extra arguments %}Some content{% endblock %}"
    django_message = snapshot("'block' tag takes only one argument")
    rusty_message = snapshot("""\
  × 'block' tag takes only one argument
   ╭────
 1 │ {% extends 'base.txt' %}{% block body with extra arguments %}Some content{% endblock %}
   ·                                       ──────────┬─────────
   ·                                                 ╰── unexpected argument(s)
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_endblock_too_many_arguments(assert_parse_error):
    template = "{% extends 'base.txt' %}{% block body %}Some content{% endblock body with extra arguments %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endblock', expected 'endblock' or 'endblock body'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × 'endblock' tag takes only one argument
   ╭────
 1 │ {% extends 'base.txt' %}{% block body %}Some content{% endblock body with extra arguments %}
   ·                                                                      ──────────┬─────────
   ·                                                                                ╰── unexpected argument(s)
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_endblock_wrong_name(assert_parse_error):
    template = (
        "{% extends 'base.txt' %}{% block body %}Some content{% endblock other %}"
    )
    django_message = snapshot(
        "Invalid block tag on line 1: 'endblock', expected 'endblock' or 'endblock body'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag 'endblock other', expected 'endblock' or 'endblock body'
   ╭────
 1 │ {% extends 'base.txt' %}{% block body %}Some content{% endblock other %}
   ·                         ────────┬───────            ──────────┬─────────
   ·                                 │                             ╰── unexpected tag
   ·                                 ╰── start tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_no_name(assert_parse_error):
    template = "{% extends %}"
    django_message = snapshot("'extends' takes one argument")
    rusty_message = snapshot("""\
  × Expected an argument
   ╭────
 1 │ {% extends %}
   · ──────┬──────
   ·       ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_extra_argument(assert_parse_error):
    template = "{% extends 'base.txt' extra %}"
    django_message = snapshot("'extends' takes one argument")
    rusty_message = snapshot("""\
  × Unexpected positional argument
   ╭────
 1 │ {% extends 'base.txt' extra %}
   ·                       ──┬──
   ·                         ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_duplicate_block(assert_parse_error):
    template = "{% extends 'base.txt' %}{% block foo %}{% endblock foo %}{% block foo %}{% endblock foo %}"
    django_message = snapshot("'block' tag with name 'foo' appears more than once")
    rusty_message = snapshot("""\
  × \n\
   ╭────
 1 │ {% extends 'base.txt' %}{% block foo %}{% endblock foo %}{% block foo %}{% endblock foo %}
   ·                         ───────┬───────                  ───────┬───────
   ·                                │                                ╰── duplicate here
   ·                                ╰── first here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_duplicate_block(assert_parse_error):
    template = "{% block foo %}{% endblock foo %}{% block foo %}{% endblock foo %}"
    django_message = snapshot("'block' tag with name 'foo' appears more than once")
    rusty_message = snapshot("""\
  × \n\
   ╭────
 1 │ {% block foo %}{% endblock foo %}{% block foo %}{% endblock foo %}
   · ───────┬───────                  ───────┬───────
   ·        │                                ╰── duplicate here
   ·        ╰── first here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_unexpected_endblock(assert_parse_error):
    template = "{% extends 'base.txt' %}{% endblock foo %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endblock'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag 'endblock foo'
   ╭────
 1 │ {% extends 'base.txt' %}{% endblock foo %}
   ·                         ─────────┬────────
   ·                                  ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_extends_int(template_engine):
    template = "{% extends 1 %}"

    if template_engine.name == "rusty":
        with pytest.raises(TemplateSyntaxError) as exc_info:
            template_engine.from_string(template)
        assert str(exc_info.value) == snapshot("""\
  × Template name must be a string or a variable
   ╭────
 1 │ {% extends 1 %}
   ·            ┬
   ·            ╰── here
   ╰────
""")

    else:
        template = template_engine.from_string(template)
        with pytest.raises(TypeError) as exc_info:
            template.render({})
        assert str(exc_info.value) == snapshot(
            "join() argument must be str, bytes, or os.PathLike object, not 'int'"
        )


def test_extends_float(template_engine):
    template = "{% extends 1.2 %}"

    if template_engine.name == "rusty":
        with pytest.raises(TemplateSyntaxError) as exc_info:
            template_engine.from_string(template)
        assert str(exc_info.value) == snapshot("""\
  × Template name must be a string or a variable
   ╭────
 1 │ {% extends 1.2 %}
   ·            ─┬─
   ·             ╰── here
   ╰────
""")

    else:
        template = template_engine.from_string(template)
        with pytest.raises(TypeError) as exc_info:
            template.render({})
        assert str(exc_info.value) == snapshot(
            "join() argument must be str, bytes, or os.PathLike object, not 'float'"
        )
