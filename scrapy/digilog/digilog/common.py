from typing import List, Tuple

from urllib3.util import parse_url

from .pipelines import normalize_url


def get_domain_and_url(original_url: str) -> Tuple[str, str]:
    parsed_url = parse_url(original_url)
    domain = '.'.join(parsed_url.host.split('.')[-2:])
    scheme = parsed_url.scheme or 'http'
    normalized_url = scheme + '://' + normalize_url(original_url)
    return domain, normalized_url


def stats_to_nested_dict(scrapy_stats: dict) -> dict:
    nested_stats = {}
    for composite_key, value in scrapy_stats.items():
        add_partial_key(nested_stats, value, composite_key.split('/'))
    return nested_stats


def add_partial_key(result_dict: dict, value, partial_keys: List[str]):
    if len(partial_keys) == 1:
        result_dict[partial_keys[0]] = value
    else:
        sub_dict = result_dict.setdefault(partial_keys[0], {})
        add_partial_key(sub_dict, value, partial_keys[1:])
