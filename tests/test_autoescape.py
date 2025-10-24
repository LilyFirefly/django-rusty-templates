from django.utils.safestring import mark_safe


def test_mark_safe(assert_render):
    html = mark_safe("<p>Hello World!</p>")
    template = "{{ html }}"
    expected = "<p>Hello World!</p>"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_autoescape(assert_render):
    html = "<p>Hello World!</p>"
    template = "{{ html }}"
    expected = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_autoescape_not_string(assert_render):
    class Html:
        def __init__(self, html):
            self.html = html

        def __str__(self):
            return self.html

    html = Html("<p>Hello World!</p>")
    template = "{{ html }}"
    expected = "&lt;p&gt;Hello World!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_autoescape_invalid_str_method(assert_render_error):
    class Broken:
        def __str__(self):
            1 / 0

    broken = Broken()
    assert_render_error(
        template="{{ broken }}",
        context={"broken": broken},
        exception=ZeroDivisionError,
        django_message="division by zero",
        rusty_message="division by zero",
    )


def test_autoescape_invalid_html_method(assert_render_error):
    class Broken(str):
        def __html__(self):
            1 / 0

    broken = Broken("")
    assert_render_error(
        template="{{ broken }}",
        context={"broken": broken},
        exception=ZeroDivisionError,
        django_message="division by zero",
        rusty_message="division by zero",
    )


def test_mark_safe_filter_lower(assert_render):
    html = mark_safe("<p>Hello World!</p>")
    template = "{{ html|lower }}"
    expected = "<p>hello world!</p>"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_autoescape_filter_lower(assert_render):
    html = "<p>Hello World!</p>"
    template = "{{ html|lower }}"
    expected = "&lt;p&gt;hello world!&lt;/p&gt;"
    assert_render(template=template, context={"html": html}, expected=expected)


def test_safe_lower(assert_render):
    html = "<p>Hello World!</p>"
    template = "{{ html|safe|lower }}"
    expected = "<p>hello world!</p>"
    assert_render(template=template, context={"html": html}, expected=expected)
