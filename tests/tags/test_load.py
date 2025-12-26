from inline_snapshot import snapshot
import pytest


def test_load_empty(assert_render):
    template = "{% load %}"
    assert_render(template=template, context={}, expected="")


def test_load_missing(assert_parse_error):
    template = "{% load missing_filters %}"
    django_message = snapshot("""\
'missing_filters' is not a registered tag library. Must be one of:
cache
custom_filters
custom_tags
i18n
invalid_tags
l10n
more_filters
no_filters
no_tags
static
tz""")
    rusty_message = snapshot("""\
  × 'missing_filters' is not a registered tag library.
   ╭────
 1 │ {% load missing_filters %}
   ·         ───────┬───────
   ·                ╰── here
   ╰────
  help: Must be one of:
        cache
        custom_filters
        custom_tags
        i18n
        invalid_tags
        l10n
        more_filters
        no_filters
        no_tags
        static
        tz
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_load_missing_filter(assert_parse_error):
    template = "{% load missing from custom_filters %}"
    django_message = snapshot(
        "'missing' is not a valid tag or filter in tag library 'custom_filters'"
    )
    rusty_message = snapshot("""\
  × 'missing' is not a valid tag or filter in tag library 'custom_filters'
   ╭────
 1 │ {% load missing from custom_filters %}
   ·         ───┬───      ───────┬──────
   ·            │                ╰── library
   ·            ╰── tag or filter
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_unknown_filter(assert_parse_error):
    template = "{{ foo|bar }}"
    django_message = snapshot("Invalid filter: 'bar'")
    rusty_message = snapshot("""\
  × Invalid filter: 'bar'
   ╭────
 1 │ {{ foo|bar }}
   ·        ─┬─
   ·         ╰── here
   ╰────
""")
    assert_parse_error(
        template=template, django_message=django_message, rusty_message=rusty_message
    )


def test_load_no_filters(template_engine):
    template = "{% load no_filters %}"

    with pytest.raises(AttributeError):
        template_engine.from_string(template)


def test_load_no_tags(template_engine):
    template = "{% load no_tags %}"

    with pytest.raises(AttributeError):
        template_engine.from_string(template)
