from django.template.loader import get_template


def render(template, context, *, using):
    template = get_template(template, using=using)
    return template.render(context)


class BrokenDunderStr:
    def __str__(self):
        1 / 0


class BrokenDunderHtml(str):
    def __html__(self):
        1 / 0


class BrokenDunderBool:
    def __bool__(self):
        1 / 0
