import pytest
from django.template import TemplateSyntaxError
from inline_snapshot import snapshot

from django_rusty_templates import RustyTemplates


def test_extends_locmem_loader(engine_class):
    template = "{{ }}"
    loaders = [
        (
            "django.template.loaders.locmem.Loader",
            {"template": template},
        ),
    ]
    config = {
        "OPTIONS": {"loaders": loaders},
        "NAME": "locmem",
        "DIRS": (),
        "APP_DIRS": False,
    }
    engine = engine_class(config)

    with pytest.raises(TemplateSyntaxError) as exc_info:
        engine.get_template("template")

    if engine_class == RustyTemplates:
        assert str(exc_info.value) == snapshot("""\
  × Empty variable tag
   ╭─[template:1:1]
 1 │ {{ }}
   · ──┬──
   ·   ╰── here
   ╰────
""")
    else:
        assert str(exc_info.value) == snapshot("Empty variable tag on line 1")
