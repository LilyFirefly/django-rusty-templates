from inline_snapshot import snapshot


def test_extends_no_blocks(assert_render):
    template = "{% extends 'basic.txt' %}"
    assert_render(template=template, context={"user": "Lily"}, expected="Hello Lily!\n")


def test_extends(assert_render):
    template = "{% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
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
    template = (
        "{# Comment #}{% extends 'base.txt' %}{% block body %}Some content{% endblock body %}"
    )
    assert_render(
        template=template, context={}, expected="# Header\nSome content\n"
    )


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
