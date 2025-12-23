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


def get_rusty_error(template, header, target, sub_label="here"):
    """
    Automated Miette-style error generator.
    """
    offset = template.find(target)
    if offset == -1:
        offset = 0

    width = len(target)

    side_dashes_count = (width - 1) // 2
    side_dashes = "─" * side_dashes_count
    pointer = f"{side_dashes}┬{side_dashes}"

    label_padding = " " * (offset + side_dashes_count)
    padding = " " * offset

    return f"""\
  × {header}
   ╭────
 1 │ {template}
   · {padding}{pointer}
   · {label_padding}╰── {sub_label}
   ╰────
"""
