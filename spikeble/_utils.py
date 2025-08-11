import inspect, textwrap


def func_to_string(fn):
    lines, _ = inspect.getsourcelines(fn)  # full function source as lines
    body = textwrap.dedent("".join(lines[1:]))  # drop function name
    return body.encode("utf-8")
