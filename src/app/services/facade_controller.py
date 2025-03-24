import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum

from fastapi import HTTPException
from starlette import status

from app import AppConst
from app.common.logger_common import log_exception
from app.models.dto import SearchCategory, CategoryMatch
from app.models.dto_v3 import ExtractorResponse
from app.models.shooter_dto import ShooterDto, ShooterStatus
from app.services.cloud_service import CloudService
from app.services.facade_service import ExtractorService, FacadeService
from app.services.mongo_service import MongoService
from app.services.ranker_controller import MatchRanker
from app.storage.storage_utils import CloudStorage


class Mode(Enum):
    FACADE = 'FACADE'
    CLOUD = 'CLOUD'
    FULL = 'FULL'


class Stage(Enum):
    # Full execution, return the results till the end
    SINGLE = 'SINGLE'
    # Return immediately
    TWO = 'TWO'


class FacadeController:
    def __init__(
            self,
            storage: CloudStorage, bucket: str, path: str, env: str,
            request_id: str = '',
            cloud_item_cap: int = AppConst.CLOUD_ITEM_CAP_W_SINGLE_STORAGE
    ):
        self.storage: CloudStorage = storage
        self.bucket: str = bucket
        self.path: str = path
        self.env: str = env
        self.cloud_item_cap = cloud_item_cap

        self.uri: str = self.storage.to_uri(self.bucket, self.path)
        self.shooter: ShooterDto = ShooterDto(
            request_id=request_id,
            response_id=str(uuid.uuid4())
        )

    async def execute_flow(
            self,
            mode: Mode,
            stage: Stage,
            min_box: float,
            prompts: str,
            rmbg: bool
    ) -> ShooterDto:
        ExtractorService.wake_up_extractors_non_blocking()
        await self.insert_doc(mode)
        if stage == Stage.SINGLE:
            await self.executing_flow(mode, stage, min_box, prompts, rmbg)
        else:
            self.cloud_item_cap = AppConst.CLOUD_ITEM_CAP_W_MULTI_STORAGE
            asyncio.create_task(self.executing_flow(mode, stage, min_box, prompts, rmbg))
        return self.shooter

    async def executing_flow(
            self,
            mode: Mode,
            stage: Stage,
            min_box: float,
            prompts: str,
            rmbg: bool
    ):
        _extractor_response: ExtractorResponse | None = None
        _matches: list[CategoryMatch] = []
        _omissions: list[dict] = []
        _keywords: list[str] = []

        _at: datetime = datetime.now(timezone.utc)
        _dur: list[int] = []
        _error: str = ''
        try:
            if mode == Mode.FACADE:
                _extractor_response, _faiss_category, _lens_dto, _custom_search_dto = await self.exec_facade(
                    min_box, prompts, rmbg
                )
            else:
                run_searchers = mode == Mode.FULL
                _extractor_response, _faiss_category, _lens_dto, _custom_search_dto, _keywords = await self.exec_full(
                    run_searchers, min_box, prompts, rmbg
                )

            _matches.extend(_faiss_category.matches)
            _omissions.extend(_faiss_category.omissions)
            _dur.append((datetime.now(timezone.utc) - _at).microseconds)

            if stage != Stage.SINGLE:
                self.update_doc(_dur, _extractor_response, _matches, _omissions, _keywords, _error)

            _img_features = _extractor_response.extraction[0].features
            _cloud_category = await CloudService.conclude_cloud(
                _img_features, _lens_dto, _custom_search_dto, self.env, self.shooter.response_id, self.cloud_item_cap
            )

            _matches.extend(_cloud_category.matches)
            _omissions.extend(_cloud_category.omissions)
            _dur.append((datetime.now(timezone.utc) - _at).microseconds)
            self.shooter.ranks.extend(MatchRanker.ranks_000(_matches))
            self.shooter.status = ShooterStatus.COMPLETE

        except Exception as e:
            _error = f'{type(e)}: {str(e)}'
            log_exception(f'FacadeController | {self.shooter.response_id}')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f'FacadeError | {_error}'
            )

        finally:
            self.update_doc(_dur, _extractor_response, _matches, _omissions, _keywords, _error)

    async def insert_doc(
            self,
            mode: Mode
    ):
        doc = {
            '_id': self.shooter.response_id,
            '_at': datetime.now(timezone.utc),
            '_dur': [],
            '_ver': AppConst.DOC_VER,
            'input': {
                'reqId': self.shooter.request_id,
                'uri': self.uri,
                'mode': mode.value,
                'domainVer': AppConst.DOMAIN_VER,
                'cloudItemSoftCap': self.cloud_item_cap
            }
        }

        await MongoService.insert_facade_doc(env=self.env, doc=doc)

    def update_doc(
            self,
            dur: list[int],
            extractor_response: ExtractorResponse | None,
            matches: list[CategoryMatch],
            omissions: list[dict],
            keywords: list[str],
            error: str
    ):
        doc = {
            '_dur': dur,
            'detection': extractor_response.to_detect_dict() if extractor_response is not None else {},
            'matches': [match.to_db_dict() for match in matches],
            'omissions': omissions,
            'keywords': keywords
        }
        if error:
            doc['error'] = error

        asyncio.create_task(MongoService.update_facade_doc(env=self.env, doc=doc, session_id=self.shooter.response_id))

    async def exec_full(
            self,
            run_searchers: bool,
            min_box: float,
            prompts: str,
            rmbg: bool
    ) -> tuple[ExtractorResponse, SearchCategory, dict, dict, list]:
        facade_task = FacadeService.extract_and_search(
            self.env, self.shooter.response_id, self.uri, prompts, min_box, rmbg, run_searchers
        )
        lens_task = FacadeService.cloud_execution_lens(
            self.storage, self.bucket, self.path, AppConst.WHITELIST_DOMAINS
        )
        vision_task = FacadeService.cloud_execution_vision(
            self.storage, self.bucket, self.path, AppConst.WHITELIST_DOMAINS
        )
        gathered = await asyncio.gather(
            facade_task, lens_task, vision_task, return_exceptions=True
        )

        if isinstance(gathered[0], Exception):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(gathered[0])
            )
        else:
            t1, t2 = gathered[0]
            extractor_response: ExtractorResponse = t1
            faiss_category: SearchCategory = t2

        lens_dto = {'matches': [], 'omissions': []}
        custom_search_dto = {'matches': [], 'omissions': []}
        keywords = []

        if isinstance(gathered[1], tuple):
            t1, t2, t3 = gathered[1]
            lens_dto.update(t1)
            custom_search_dto.update(t2)
            keywords.extend(t3)

        if isinstance(gathered[2], tuple):
            t1, t2 = gathered[2]
            vision_custom_search_dto: dict = t1
            vision_keywords: list[str] = t2
            custom_search_dto.update(vision_custom_search_dto)
            keywords.extend(vision_keywords)

        return extractor_response, faiss_category, lens_dto, custom_search_dto, keywords

    async def exec_facade(
            self,
            min_box: float,
            prompts: str,
            rmbg: bool
    ) -> tuple[ExtractorResponse, SearchCategory, dict, dict]:
        try:
            extractor_response, faiss_category = await FacadeService.extract_and_search(
                self.env, self.shooter.response_id, self.uri, prompts, min_box, rmbg
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )

        return extractor_response, faiss_category, {'matches': [], 'omissions': []}, {'matches': [], 'omissions': []}
