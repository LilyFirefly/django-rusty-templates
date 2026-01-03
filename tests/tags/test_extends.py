from inline_snapshot import snapshot


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
