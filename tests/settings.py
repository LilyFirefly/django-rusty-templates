import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INSTALLED_APPS = [
    "tests.apps.DummyAppConfig",
    "django.contrib.contenttypes",
    "django.contrib.auth",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["tests/templates"],
        "OPTIONS": {
            "libraries": {
                "custom_filters": "tests.templatetags.custom_filters",
                "custom_tags": "tests.templatetags.custom_tags",
                "more_filters": "tests.templatetags.more_filters",
                "no_filters": "tests.templatetags.no_filters",
                "no_tags": "tests.templatetags.no_tags",
            },
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
    {
        "BACKEND": "django_rusty_templates.RustyTemplates",
        "DIRS": ["tests/templates"],
        "NAME": "rusty",
        "OPTIONS": {
            "libraries": {
                "custom_filters": "tests.templatetags.custom_filters",
                "custom_tags": "tests.templatetags.custom_tags",
                "more_filters": "tests.templatetags.more_filters",
                "no_filters": "tests.templatetags.no_filters",
                "no_tags": "tests.templatetags.no_tags",
            },
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
            ],
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "NAME": "django_nocache",
        "OPTIONS": {
            "loaders": [
                ("django.template.loaders.filesystem.Loader", ["tests/templates"])
            ],
        },
    },
    {
        "BACKEND": "django_rusty_templates.RustyTemplates",
        "NAME": "rusty_nocache",
        "OPTIONS": {
            "loaders": [
                ("django.template.loaders.filesystem.Loader", ["tests/templates"])
            ],
        },
    },
]

ROOT_URLCONF = "tests.urls"

USE_I18N = True
USE_L10N = True
LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"
USE_TZ = False
