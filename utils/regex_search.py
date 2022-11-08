import re


def regex_search_between(page_content: str, first_pair: str, second_pair: str):
    result = re.search(f'{first_pair}(.*){second_pair}', page_content)
    if not result:
        return
    return result.group(1)

