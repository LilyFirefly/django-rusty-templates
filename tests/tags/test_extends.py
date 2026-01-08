from inline_snapshot import snapshot


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
