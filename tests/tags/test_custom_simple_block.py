from inline_snapshot import snapshot
from django.template.base import VariableDoesNotExist


def test_simple_block_tag_repeat(assert_render):
    template = "{% load repeat from custom_tags %}{% repeat 5 %}foo{% endrepeat %}"
    assert_render(template=template, context={}, expected="foofoofoofoofoo")


def test_simple_block_tag_repeat_as(assert_render):
    template = "{% load repeat from custom_tags %}{% repeat 2 as bar %}foo{% endrepeat %}{{ bar }}{{ bar|upper }}"
    assert_render(template=template, context={}, expected="foofooFOOFOO")


def test_with_block(assert_render):
    template = "{% load with_block from custom_tags %}{% with_block var='name' %}{{ user }}{% end_with_block %}{{ name|lower }}"
    context = {"user": "Lily"}
    assert_render(template=template, context=context, expected="lily")


def test_simple_block_tag_missing_context(assert_parse_error):
    template = "{% load missing_context_block from invalid_tags %}{% missing_context_block %}{% end_missing_context_block %}"
    django_message = snapshot(
        "'missing_context_block' is decorated with takes_context=True so it must have a first argument of 'context' and a second argument of 'content'"
    )
    rusty_message = snapshot("""\
  × 'missing_context_block' is decorated with takes_context=True so it must
  │ have a first argument of 'context' and a second argument of 'content'
   ╭────
 1 │ {% load missing_context_block from invalid_tags %}{% missing_context_block %}{% end_missing_context_block %}
   ·         ──────────┬──────────
   ·                   ╰── loaded here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_missing_content(assert_parse_error):
    template = "{% load missing_content_block from invalid_tags %}{% missing_content_block %}{% end_missing_content_block %}"
    django_message = snapshot(
        "'missing_content_block' must have a first argument of 'content'"
    )
    rusty_message = snapshot("""\
  × 'missing_content_block' must have a first argument of 'content'
   ╭────
 1 │ {% load missing_content_block from invalid_tags %}{% missing_content_block %}{% end_missing_content_block %}
   ·         ──────────┬──────────
   ·                   ╰── loaded here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_missing_content_takes_context(assert_parse_error):
    template = "{% load missing_content_block_with_context from invalid_tags %}{% missing_content_block_with_context %}{% end_missing_content_block_with_context %}"
    django_message = snapshot(
        "'missing_content_block_with_context' is decorated with takes_context=True so it must have a first argument of 'context' and a second argument of 'content'"
    )
    rusty_message = snapshot("""\
  × 'missing_content_block_with_context' is decorated with takes_context=True
  │ so it must have a first argument of 'context' and a second argument of
  │ 'content'
   ╭────
 1 │ {% load missing_content_block_with_context from invalid_tags %}{% missing_content_block_with_context %}{% end_missing_content_block_with_context %}
   ·         ─────────────────┬────────────────
   ·                          ╰── loaded here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_missing_end_tag(assert_parse_error):
    template = "{% load repeat from custom_tags %}{% repeat 3 %}"
    django_message = snapshot(
        "Unclosed tag on line 1: 'repeat'. Looking for one of: endrepeat."
    )
    rusty_message = snapshot("""\
  × Unclosed 'repeat' tag. Looking for one of: endrepeat
   ╭────
 1 │ {% load repeat from custom_tags %}{% repeat 3 %}
   ·                                   ───────┬──────
   ·                                          ╰── started here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_end_tag_only(assert_parse_error):
    template = "{% load repeat from custom_tags %}{% endrepeat %}"
    django_message = snapshot(
        "Invalid block tag on line 1: 'endrepeat'. Did you forget to register or load this tag?"
    )
    rusty_message = snapshot("""\
  × Unexpected tag endrepeat
   ╭────
 1 │ {% load repeat from custom_tags %}{% endrepeat %}
   ·                                   ───────┬───────
   ·                                          ╰── unexpected tag
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_missing_argument(assert_render_error):
    django_message = snapshot("can't multiply sequence by non-int of type 'str'")
    rusty_message = snapshot("""\
  × can't multiply sequence by non-int of type 'str'
   ╭────
 1 │ {% load repeat from custom_tags %}{% repeat five %}{% endrepeat %}
   ·                                   ────────┬────────
   ·                                           ╰── here
   ╰────
""")

    assert_render_error(
        template="{% load repeat from custom_tags %}{% repeat five %}{% endrepeat %}",
        context={},
        exception=TypeError,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_simple_block_tag_invalid_argument(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [five] in [{'True': True, 'False': False, 'None': None}, {}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [five] in {"False": False, "None": None, "True":
  │ True}
   ╭────
 1 │ {% load repeat from custom_tags %}{% repeat five|default:five %}{% endrepeat %}
   ·                                                          ──┬─
   ·                                                            ╰── key
   ╰────
""")
    assert_render_error(
        template="{% load repeat from custom_tags %}{% repeat five|default:five %}{% endrepeat %}",
        context={},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )


def test_simple_block_tag_argument_syntax_error(assert_parse_error):
    template = "{% load repeat from custom_tags %}{% repeat a= %}{% endrepeat %}"
    django_message = snapshot("Could not parse the remainder: '=' from 'a='")
    rusty_message = snapshot("""\
  × Incomplete keyword argument
   ╭────
 1 │ {% load repeat from custom_tags %}{% repeat a= %}{% endrepeat %}
   ·                                             ─┬
   ·                                              ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_simple_block_tag_content_render_error(assert_render_error):
    django_message = snapshot(
        "Failed lookup for key [bar] in [{'True': True, 'False': False, 'None': None}, {}]"
    )
    rusty_message = snapshot("""\
  × Failed lookup for key [bar] in {"False": False, "None": None, "True":
  │ True}
   ╭────
 1 │ {% load repeat from custom_tags %}{% repeat 2 %}{{ foo|default:bar }}{% endrepeat %}
   ·                                                                ─┬─
   ·                                                                 ╰── key
   ╰────
""")
    assert_render_error(
        template="{% load repeat from custom_tags %}{% repeat 2 %}{{ foo|default:bar }}{% endrepeat %}",
        context={},
        exception=VariableDoesNotExist,
        django_message=django_message,
        rusty_message=rusty_message,
    )
