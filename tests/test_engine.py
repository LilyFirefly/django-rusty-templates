from pathlib import Path

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.template import engines, Context
from django.template.engine import Engine
from django.template.library import InvalidTemplateLibrary
from django.template.exceptions import TemplateDoesNotExist
from django_rusty_templates import RustyTemplates


def test_import_libraries_import_error():
    params = {"libraries": {"import_error": "invalid.path"}}
    expected = "Invalid template library specified. ImportError raised when trying to load 'invalid.path': No module named 'invalid'"

    with pytest.raises(InvalidTemplateLibrary) as exc_info:
        Engine(**params)

    assert str(exc_info.value) == expected

    with pytest.raises(InvalidTemplateLibrary) as exc_info:
        RustyTemplates(
            {"OPTIONS": params, "NAME": "rust", "DIRS": [], "APP_DIRS": False}
        )

    assert str(exc_info.value) == expected


def test_import_libraries_no_register():
    params = {"libraries": {"no_register": "tests"}}
    expected = "Module  tests does not have a variable named 'register'"

    with pytest.raises(InvalidTemplateLibrary) as exc_info:
        Engine(**params)

    assert str(exc_info.value) == expected

    expected = "Module 'tests' does not have a variable named 'register'"
    with pytest.raises(InvalidTemplateLibrary) as exc_info:
        RustyTemplates(
            {"OPTIONS": params, "NAME": "rust", "DIRS": [], "APP_DIRS": False}
        )

    assert str(exc_info.value) == expected


def test_import_libraries_module_error():
    params = {"libraries": {"zero_division": "tests.zero_division"}}

    with pytest.raises(ZeroDivisionError):
        Engine(**params)

    with pytest.raises(ZeroDivisionError):
        RustyTemplates(
            {"OPTIONS": params, "NAME": "rust", "DIRS": [], "APP_DIRS": False}
        )


def test_pathlib_dirs():
    engine = RustyTemplates(
        {
            "NAME": "rust",
            "OPTIONS": {},
            "DIRS": [Path(settings.BASE_DIR) / "templates"],
            "APP_DIRS": False,
        }
    )

    context = {"user": "Lily"}
    expected = "Hello Lily!\n"

    template = engine.get_template("basic.txt")
    assert template.render(context) == expected


def test_select_template_first_exists():
    template = engines["rusty"].engine.select_template(
        ["basic.txt", "full_example.html"]
    )
    assert template.render({"user": "Lily"}) == "Hello Lily!\n"

    template = engines["django"].engine.select_template(
        ["basic.txt", "full_example.html"]
    )
    assert template.render(Context({"user": "Lily"})) == "Hello Lily!\n"


def test_select_template_second_exists():
    template = engines["rusty"].engine.select_template(["nonexistent.txt", "basic.txt"])
    assert template.render({"user": "Lily"}) == "Hello Lily!\n"

    template = engines["django"].engine.select_template(
        ["nonexistent.txt", "basic.txt"]
    )
    assert template.render(Context({"user": "Lily"})) == "Hello Lily!\n"


@pytest.mark.parametrize(
    "template_list,expected_error",
    [
        pytest.param([], "No template names provided", id="Empty list"),
        pytest.param(
            ["nonexistent1.txt", "nonexistent2.txt"],
            "nonexistent1.txt, nonexistent2.txt",
            id="None exist",
        ),
    ],
)
def test_select_template_errors(template_engine, template_list, expected_error):
    with pytest.raises(TemplateDoesNotExist) as exc_info:
        template_engine.engine.select_template(template_list)

    assert str(exc_info.value) == expected_error


def test_select_template_invalid(template_engine):
    with pytest.raises(UnicodeError):
        template_engine.engine.select_template(["invalid.txt"])


@pytest.mark.parametrize(
    "loaders,template_name,expected",
    [
        pytest.param(
            [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Top-level list of loaders",
        ),
        pytest.param(
            (
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ),
            "basic.txt",
            "Hello Lily!\n",
            id="Top-level tuple of loaders",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Cached loader with list args",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    (
                        "django.template.loaders.filesystem.Loader",
                        "django.template.loaders.app_directories.Loader",
                    ),
                ),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Cached loader with tuple args",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        ("django.template.loaders.filesystem.Loader", ["tests", "app"]),
                        "django.template.loaders.app_directories.Loader",
                    ],
                ),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Cached loader + Filesystem Loader with list dirs",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    (
                        ("django.template.loaders.filesystem.Loader", ("tests", "app")),
                        "django.template.loaders.app_directories.Loader",
                    ),
                ),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Cached loader + Filesystem Loader with tuple dirs",
        ),
        pytest.param(
            [
                ("django.template.loaders.filesystem.Loader", ["tests/templates"]),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Filesystem loader with list dirs",
        ),
        pytest.param(
            [
                ("django.template.loaders.filesystem.Loader", ("tests/templates",)),
            ],
            "basic.txt",
            "Hello Lily!\n",
            id="Filesystem loader with tuple dirs",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.locmem.Loader",
                    {"index.html": "Welcome {{ user }}!"},
                ),
            ],
            "index.html",
            "Welcome Lily!",
            id="Locmem Loader with dict",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    [
                        (
                            "django.template.loaders.locmem.Loader",
                            {"nested.html": "Nested {{ user }}!"},
                        ),
                    ],
                ),
            ],
            "nested.html",
            "Nested Lily!",
            id="Cached loader with nested Locmem",
        ),
    ],
)
def test_loader_configurations(loaders, template_name, expected):
    engine = RustyTemplates(
        {
            "OPTIONS": {"loaders": loaders},
            "NAME": "rust",
            "DIRS": [],
            "APP_DIRS": False,
        }
    )

    context = {"user": "Lily"}
    template = engine.get_template(template_name)
    assert template.render(context) == expected


@pytest.mark.parametrize(
    "loaders,error_message",
    [
        pytest.param(
            [()],
            "Invalid template loader: (). Configuration is empty",
            id="Empty tuple loader configuration",
        ),
        pytest.param(
            [[]],
            "Invalid template loader: []. Configuration is empty",
            id="Empty list loader configuration",
        ),
        pytest.param(
            [(123, "arg")],
            "Invalid template loader: (123, 'arg'). First element of tuple configuration must be a Loader class name",
            id="Non-string first element (int)",
        ),
        pytest.param(
            [([1, 2, 3], "arg")],
            "Invalid template loader: ([1, 2, 3], 'arg'). First element of tuple configuration must be a Loader class name",
            id="Non-string first element (list)",
        ),
        pytest.param(
            [({"key": "value"}, "arg")],
            "Invalid template loader: ({'key': 'value'}, 'arg'). First element of tuple configuration must be a Loader class name",
            id="Non-string first element (dict)",
        ),
        pytest.param(
            ["django.template.loaders.cached.Loader"],
            "django.template.loaders.cached.Loader requires a list/tuple of loaders",
            id="Empty cached loader",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    [()],
                )
            ],
            "Invalid template loader: (). Configuration is empty",
            id="Nested empty tuple in cached loader",
        ),
        pytest.param(
            [
                (
                    "django.template.loaders.cached.Loader",
                    [(123, "arg")],
                )
            ],
            "Invalid template loader: (123, 'arg'). First element of tuple configuration must be a Loader class name",
            id="Nested non-string first element in cached loader",
        ),
        pytest.param(
            [123],
            "Invalid template loader: 123. 'int' object is not iterable",
            id="Non-iterable loader (int)",
        ),
        pytest.param(
            ["123"],
            "Invalid template loader class: 123",
            id="Invalid loader class",
        ),
        pytest.param(
            [{"key": "value"}],
            "Invalid template loader: {'key': 'value'}. Missing second element in tuple configuration",
            id="Dict as loader configuration",
        ),
    ],
)
def test_invalid_loader_configurations(loaders, error_message):
    """Test that invalid loader configurations raise appropriate errors."""
    with pytest.raises(ImproperlyConfigured) as exc_info:
        RustyTemplates(
            {
                "OPTIONS": {"loaders": loaders},
                "NAME": "rust",
                "DIRS": [],
                "APP_DIRS": False,
            }
        )

    assert error_message == str(exc_info.value)


def test_valid_file_charset():
    RustyTemplates(
        {
            "OPTIONS": {"file_charset": "utf-8"},
            "NAME": "rust",
            "DIRS": [],
            "APP_DIRS": False,
        }
    )


def test_invalid_file_charset():
    with pytest.raises(ValueError) as exc_info:
        RustyTemplates(
            {
                "OPTIONS": {"file_charset": "not-a-real-encoding"},
                "NAME": "rust",
                "DIRS": [],
                "APP_DIRS": False,
            }
        )

    assert "Unknown encoding: 'not-a-real-encoding'" == str(exc_info.value)


def test_render_to_string_success():
    rusty_engine = engines["rusty"]

    # Test with single template name
    result = rusty_engine.engine.render_to_string("basic.txt", {"user": "Alice"})
    assert result == "Hello Alice!\n"

    # Test with template list/tuple
    result = rusty_engine.engine.render_to_string(
        ["nonexistent.html", "basic.txt"], {"user": "Bob"}
    )
    assert result == "Hello Bob!\n"
    result = rusty_engine.engine.render_to_string(
        ("nonexistent.html", "basic.txt"), {"user": "Bob"}
    )
    assert result == "Hello Bob!\n"

    # Test with no context
    result = rusty_engine.engine.render_to_string("basic.txt")
    assert result == "Hello !\n"


@pytest.mark.parametrize(
    "template_name,message",
    [
        ({"nonexistent.html", "basic.txt"}, "'set' object is not an instance of 'str'"),
        ([1, 2], "'int' object is not an instance of 'str'"),
        (None, "'None' is not an instance of 'str'"),
    ],
)
def test_render_to_string_invalid_template_name(template_name, message):
    rusty_engine = engines["rusty"]
    with pytest.raises(TypeError) as exc_info:
        rusty_engine.engine.render_to_string(template_name, {"user": "Bob"})

    assert str(exc_info.value) == message


def test_render_to_string_no_valid_template():
    rusty_engine = engines["rusty"]
    with pytest.raises(TemplateDoesNotExist):
        rusty_engine.engine.render_to_string(
            ("nonexistent.html", "nonexistent2.html"), {"user": "Bob"}
        )

    with pytest.raises(TemplateDoesNotExist):
        rusty_engine.engine.render_to_string("nonexistent.html", {"user": "Bob"})
