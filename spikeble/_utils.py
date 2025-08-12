import inspect, textwrap


def fn_to_string(fn) -> str:
    """Extract function body as a string without the function definition line."""
    lines, _ = inspect.getsourcelines(fn)  # full function source as lines
    body = textwrap.dedent("".join(lines[1:]))  # drop function name
    return body
