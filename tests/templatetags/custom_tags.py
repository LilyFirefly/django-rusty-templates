from django import template


register = template.Library()


@register.simple_tag
def double(value):
    return value * 2


@register.simple_tag
def multiply(a, b, c):
    return a * b * c


@register.simple_tag
def invert(value=2):
    return 1 / value


@register.simple_tag
def combine(*args, operation="add"):
    if operation == "add":
        return sum(args)

    if operation == "multiply":
        total = 1
        for arg in args:
            total *= arg
        return total

    raise RuntimeError("Unknown operation")


@register.simple_tag
def table(**kwargs):
    return "\n".join(f"{k}-{v}" for k, v in kwargs.items())


@register.simple_tag(name="list")
def list_items(items, *, header):
    parts = [f"# {header}"]
    for item in items:
        parts.append(f"* {item}")
    return "\n".join(parts)


@register.simple_tag(takes_context=True)
def request_path(context):
    return context.request.path


@register.simple_tag(takes_context=True)
def greeting(context, name):
    user = context.get("user", "Django")
    return f"Hello {name} from {user}!"


@register.simple_tag(takes_context=True)
def local_time(context, time):
    timezone = context["timezone"]
    return time.astimezone(timezone)


@register.simple_tag(takes_context=True)
def counter(context):
    if "count" in context:
        context["count"] += 1
    else:
        context["count"] = 1
    return ""


@register.simple_block_tag
def repeat(content, count):
    return content * count


@register.simple_block_tag(takes_context=True, end_name="end_with_block")
def with_block(context, content, *, var):
    context[var] = content
    return ""


# @register.inclusion_tag("results.html")
# def results(poll):
#    return {"choices": poll.choices}
