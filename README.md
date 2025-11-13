# Django Rusty Templates

Django Rusty Templates is an experimental reimplementation of Django's templating language in Rust.

## Goals

* 100% compatibility of rendered output.
* Error reporting that is at least as useful as Django's errors.
* Improved performance over Django's pure Python implementation.

## Installation

Django Rusty Templates is not yet ready for full release, so it is not available on PyPI yet. Instead it can be installed from github or from a local clone:

```sh
$ pip install git+https://github.com/LilyFirefly/django-rusty-templates.git
```

```sh

$ git clone git@github.com:LilyFirefly/django-rusty-templates.git
$ pip install ./django-rusty-templates
```

You will need a rust compiler installed (https://rustup.rs/).

## Usage

Add an entry to your [`TEMPLATES` setting](https://docs.djangoproject.com/en/5.1/ref/settings/#std-setting-TEMPLATES) with `"BACKEND"` set to `"django_rusty_templates.RustyTemplates"`:

```python
TEMPLATES = [
    {
        "BACKEND": "django_rusty_templates.RustyTemplates",
        ... # Other configuration options
    },
]
```

## Contributing

Django Rusty Templates is open to contributions. These can come in many forms:

* Implementing missing features, such as filters and tags built into Django.
* Reporting bugs where Django Rusty Templates gives the wrong result.
* Adding new test cases to ensure Django Rusty Templates behaves the same as Django.
* Adding benchmarks to track performance.
* Refactoring for readability or performance.

For detailed instructions on setting up your development environment and contributing to the project, please see [CONTRIBUTING.md](CONTRIBUTING.md).
