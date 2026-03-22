from inline_snapshot import snapshot


def test_unmatched_block_tag(assert_parse_error):
    template = "{% block foo %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'block'. Looking for one of: endblock."
    )
    rusty_message = snapshot("""\
  × Unclosed 'block' tag. Looking for one of: 'endblock', 'endblock foo'
   ╭────
 1 │ {% block foo %}
   · ───────┬───────
   ·        ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
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
