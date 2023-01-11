import re


def regex_search_between(page_content: str, first_pair: str, second_pair: str):
    result = re.search(f'{first_pair}(.*){second_pair}', page_content)
    if not result:
        return
    return result.group(1)


def title_regex_search_between(page_content: str, first_pair: str, second_pair: str):
    _result = re.findall(f'{first_pair}(.*?){second_pair}', page_content)
    if not _result:
        return
    result = sorted(_result, key=len)
    res = result[0]
    if len(res) > 255:
        return
    return res
