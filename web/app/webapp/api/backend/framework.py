import os
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


def get_env_str_or(name: str, fallback: str) -> str:
    try:
        return os.environ[name]
    except KeyError:
        return fallback


def get_env_int_or(name: str, fallback: int) -> int:
    return int(get_env_str_or(name, str(fallback)))
