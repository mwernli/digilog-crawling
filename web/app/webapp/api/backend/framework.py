from typing import Any, Union


def parse_int(s: Any) -> Union[int, None]:
    if s is None:
        return None
    try:
        return int(s)
    except ValueError:
        return None


def parse_int_or_default(s: Any, fallback: int) -> int:
    result = parse_int(s)
    if result is None:
        return fallback
    else:
        return result
