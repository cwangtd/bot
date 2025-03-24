import logging

from fastapi_camelcase import CamelModel
from pydantic import Field

from app.storage.storage_utils import CloudStorage

logger = logging.getLogger('main.app')


class RankItem(CamelModel):
    title: str
    score: float
    thumbnail_uri: str
    extra: dict = {
        # title: str
        # image_uri: str
        # source: str
        # pageUrl: str
        # imageUrl: str
        # etc...
    }

    def to_db_dict(self):
        return {
            **{'title': self.title, 'score': self.score, 'thumbnail_uri': self.thumbnail_uri}, **self.extra
        }

    def to_v000_response(self, cm: 'CategoryMatch'):
        return {
            'title': f'{self.title} | {cm.name}' if cm.name else self.title,
            'score': self.score,
            'url': CloudStorage.sign_uri(self.thumbnail_uri),
        }


class CategoryMatch(CamelModel):
    # The fields of key, name, and category are aligned with the source searcher
    key: str
    name: str = ''
    category: str = ''
    items: list[RankItem] = []
    extra: dict = {}

    def to_db_dict(self):
        return {
            **{'key': self.key, 'category': self.category, 'items': [item.to_db_dict() for item in self.items]},
            **self.extra
        }


class SearchCategory(CamelModel):
    matches: list[CategoryMatch] = []
    omissions: list[dict] = []

    def sort_matches_by_score(self):
        for match in self.matches:
            match.items.sort(key=lambda x: x.score, reverse=True)

    def deduplicate_by_img_url(self):
        url_set = set()
        for match in self.matches:
            unique_items = []
            items = match.items
            for item in items:
                if item.extra['imageUrl'] not in url_set:
                    unique_items.append(item)
                    url_set.add(item.extra['imageUrl'])
            match.items = unique_items

        url_set = set()
        unique_items = []
        for item in self.omissions:
            if item['imageUrl'] not in url_set:
                unique_items.append(item)
                url_set.add(item['imageUrl'])
        self.omissions = unique_items


class ExtractorMessage(CamelModel):
    env: str
    session_id: str
    uri: str

    @property
    def key(self) -> str:
        raise NotImplementedError("Subclasses must implement `key` property")

    @property
    def is_critical(self) -> bool:
        return False


class FacadeMainExtractorMessage(ExtractorMessage):
    prompts: str
    min_box: float
    rmbg: bool

    @property
    def key(self) -> str:
        return f'{self.session_id}/0'

    @property
    def is_critical(self) -> bool:
        return True


class CloudItemExtractorMessage(ExtractorMessage):
    serial: int = Field(
        default=...,
        ge=1,
        description="Serial number (1+); 0 is reserved for full-frame features in Extractor."
    )

    @property
    def key(self) -> str:
        return f'{self.session_id}/{self.serial}'
