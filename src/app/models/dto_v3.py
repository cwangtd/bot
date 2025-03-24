from fastapi_camelcase import CamelModel

from app.storage.storage_utils import CloudStorage, C_CHECK_BUCKET
from app.utils.lrucache import get_trailer_db

TRAILER_DB = get_trailer_db()


class ExtractionDto(CamelModel):
    score: float
    ratio: float
    boxes: list[int]
    features: list[float]


class ExtractorResponse(CamelModel):
    env: str
    session_id: str
    uri: str
    rmbg: bool = True
    min_box: float = 1.0
    box_prompts: str = ''
    extraction: list[ExtractionDto] = []
    image_uri: str = ''
    thumbnail_uri: str = ''
    error_code: str = ''
    error_message: str = ''

    @property
    def is_success(self):
        return self.error_code == ''

    def to_detect_dict(self):
        return {
            'minBox': self.min_box,
            'boxPrompts': self.box_prompts,
            'box': [{'score': e.score, 'ratio': e.ratio, 'boxes': e.boxes} for e in self.extraction]
        }


class SearchParam(CamelModel):
    dataset: str
    result_cap: int = 20


class SearcherVector(CamelModel):
    # All fields will be written to db. Adding/removing field cautiously.
    vid: int
    score: float

    title: str = ''
    query_field: str = ''
    thumbnail_uri: str = ''
    box_to_obj: str = ''

    def to_rank_item_dict(self) -> dict:
        doc_extra = {
            'vid': self.vid
        }
        if self.box_to_obj:
            doc_extra['boxToObj'] = self.box_to_obj
        return {
            'title': f'{self.title}',
            'score': self.score,
            'thumbnail_uri': self.thumbnail_uri,
            'extra': doc_extra
        }

    def parse_v1(self, thumbnail_dir_uri):
        video_id = hex((self.vid >> 43) & 0xFFFFF)[2:].upper()
        is_poster = (self.vid & 0x200) == 0x200
        if is_poster:
            poster_id = (self.vid >> 23) & 0x00000FFFFF
            segments = f'poster-thumbnail/{video_id}/{poster_id}'
        else:  # trailers only, in-house downloaded movies are forbidden
            frame_id = str((self.vid >> 23) & 0x00000FFFFF).zfill(6).upper()
            segments = f'key-frame-thumbnail/{video_id}/{frame_id}'

        self.query_field = video_id
        self.thumbnail_uri = f'{thumbnail_dir_uri}/{segments}.webp'

    def parse_v3(self, thumbnail_dir_uri):
        video_id = hex(self.vid)[2:].zfill(8).upper()
        self.query_field = video_id
        self.thumbnail_uri = f'{thumbnail_dir_uri}/scale-thumbnail/{video_id}.webp'

    def set_doc_extra(self, feature_box_position: int):
        if feature_box_position > 0:
            obj_id = str(int(self.vid) & 0x000000000000000F)
            self.box_to_obj = f'{str(feature_box_position).zfill(2)}-{obj_id.zfill(2)}'

    def to_omission(self, category: str) -> dict:
        return {
            'vid': self.vid,
            'score': self.score,
            'thumbnailUri': self.thumbnail_uri,
            'category': category,
        }


class SearchDataset(CamelModel):
    dataset: str
    size: int
    feature_position: int
    thumbnail_dir_uri: str
    display_name: str = ''
    vectors: list[SearcherVector] = []

    @property
    def is_movie_collection(self) -> bool:
        return self.dataset == 'video-frame' or self.dataset == 'video-poster' or self.dataset == 'video-poster-box'

    @property
    def col_name(self) -> str:
        return 'video' if self.is_movie_collection else self.dataset.replace('-', '_')

    def is_my_col_name(self, _col_name) -> bool:
        if self.is_movie_collection:
            return _col_name == 'video'
        else:
            return _col_name == self.dataset.replace('-', '_')


class SearcherResponse(CamelModel):
    search_datasets: list[SearchDataset]
    omissions: list[dict] = []

    def __init__(self, /, **data):
        if data is not None and len(data) > 0:
            super().__init__(**data)
            self.merge_video()
            self.update_and_deduplicate_vectors()
            for ss in self.search_datasets:
                ss.vectors.sort(key=lambda x: x.score, reverse=True)

    def merge_video(self):
        video_dataset = SearchDataset(
            dataset='video', size=0, feature_position=0, thumbnail_dir_uri='s3://provenance-c-check-storage-us-east-1/movie-video/scale-thumbnail'
        )
        _search_datasets = [video_dataset]

        for ss in self.search_datasets:
            if ss.is_movie_collection:
                video_dataset.size += ss.size
                video_dataset.vectors.extend(ss.vectors)
            else:
                _search_datasets.append(ss)
            for vv in ss.vectors:
                vv.set_doc_extra(ss.feature_position)
        self.search_datasets = _search_datasets

    def update_and_deduplicate_vectors(self):
        video_item_by_uri_w_highest_score_dict = {}
        for ss in self.search_datasets:
            if ss.dataset == 'video':
                for vv in ss.vectors:
                    vv.parse_v1(ss.thumbnail_dir_uri)
                    uri = vv.thumbnail_uri
                    if uri not in video_item_by_uri_w_highest_score_dict:
                        video_item_by_uri_w_highest_score_dict[uri] = vv
                    elif vv.score > video_item_by_uri_w_highest_score_dict[uri].score:
                        self.omissions.append(video_item_by_uri_w_highest_score_dict[uri].to_omission(ss.dataset))
                        video_item_by_uri_w_highest_score_dict[uri] = vv
                    else:
                        self.omissions.append(vv.to_omission(ss.dataset))
            else:
                for vv in ss.vectors:
                    vv.parse_v3(ss.thumbnail_dir_uri)

        for ss in self.search_datasets:
            if ss.dataset == 'video':
                ss.vectors = list(video_item_by_uri_w_highest_score_dict.values())
                break
