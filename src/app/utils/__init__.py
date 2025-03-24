import logging

logger = logging.getLogger('main.app')
logger.info(f'Init {__file__}')


def convert_to_omission(item) -> dict:
    return {
        'title': item['title'],
        'pageUrl': item['pageUrl'],
        'imageUrl': item['imageUrl'],
        'source': item['source']
    }


def calc_score(vector1, vector2):
    if vector1 is None or vector2 is None or len(vector1) != len(vector2):
        return -1
    inner_product = sum(i * j for i, j in zip(vector1, vector2))
    return (1 + inner_product) / 2
