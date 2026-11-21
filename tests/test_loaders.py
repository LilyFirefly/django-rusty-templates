from pathlib import Path

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


def test_origin_locmem(engine_class):
    loaders = [
        (
            "django.template.loaders.locmem.Loader",
            {"template": "content"},
        ),
    ]
    config = {
        "OPTIONS": {"loaders": loaders},
        "NAME": "locmem",
        "DIRS": (),
        "APP_DIRS": False,
    }
    engine = engine_class(config)

    template = engine.get_template("template")

    assert template.origin.name == "template"
    assert template.origin.template_name == "template"
    assert repr(template.origin) == "<Origin name='template'>"


def test_origin_filesystem(engine_class):
    config = {
        "OPTIONS": {"loaders": ["django.template.loaders.filesystem.Loader"]},
        "NAME": "filesystem",
        "DIRS": ("tests/templates",),
        "APP_DIRS": False,
    }
    engine = engine_class(config)

    template = engine.get_template("basic.txt")

    basic_path = Path("tests/templates/basic.txt").absolute()
    assert Path(template.origin.name) == basic_path
    assert template.origin.template_name == "basic.txt"
    assert repr(template.origin) == f"<Origin name={str(basic_path)!r}>"
