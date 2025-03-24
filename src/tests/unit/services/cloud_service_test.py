import time
import unittest

from app.services.cloud_service import CloudService


class TestDistributeItems(unittest.TestCase):
    @staticmethod
    def init_items(num):
        items = []
        for i in range(num):
            items.append({
                'title': f'title-{time.time_ns()}',
                'pageUrl': 'url',
                'imageUrl': 'url',
                'source': 'src',
                'extraId': i
            })
        return items

    def test_empty_matches(self):
        lens = {'matches': []}
        custom_search = {'matches': []}
        cap = 10
        result = CloudService.distribute_items(lens, custom_search, cap)
        self.assertEqual(result, [])

    def test_single_match(self):
        lens = {'matches': [{'items': self.init_items(3)}], 'omissions': []}
        custom_search = {'matches': [], 'omissions': []}
        cap = 2
        result = CloudService.distribute_items(lens, custom_search, cap)
        expected = [
            lens['matches'][0]['items'][0],
            lens['matches'][0]['items'][1]
        ]
        self.assertEqual(result, expected)

    def test_multiple_matches(self):
        lens = {'matches': [{'items': self.init_items(3)}, {'items': self.init_items(3)}], 'omissions': []}
        custom_search = {'matches': [{'items': self.init_items(3)}], 'omissions': []}
        cap = 5
        result = CloudService.distribute_items(lens, custom_search, cap)
        expected = [
            lens['matches'][0]['items'][0],
            lens['matches'][1]['items'][0],
            custom_search['matches'][0]['items'][0],
            lens['matches'][0]['items'][1],
            lens['matches'][1]['items'][1],
        ]
        self.assertEqual(result, expected)
