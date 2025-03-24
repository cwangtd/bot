import asyncio
import logging
import time

from fastapi import HTTPException
from pymilvus import MilvusClient
from starlette import status

from app import get_settings, get_searcher_dict
from app.common.http_async_builder import HttpAsyncBuilder
from app.common.logger_common import log_exception, timed_plus
from app.exceptions.RedisPollError import RedisPollError
from app.models.dto import SearchCategory, CategoryMatch, RankItem, FacadeMainExtractorMessage, ExtractorMessage
from app.models.dto_v3 import ExtractorResponse, SearcherResponse, SearchDataset, SearcherVector
from app.services.aws_service import AwsService
from app.services.cloud_custom_search_helper import exec_custom_search
from app.services.cloud_lens_helper import LENS_HELPER
from app.services.cloud_vision_help import VisionHelper
from app.services.mongo_service import MongoService
from app.storage.storage_utils import CloudStorage

logger = logging.getLogger('main.app')


class FacadeService:

    @staticmethod
    async def extract_and_search(
            env: str,
            session_id: str,
            uri: str,
            prompts: str,
            min_box: float,
            rmbg: bool,
            run_searchers: bool = True
    ) -> tuple[ExtractorResponse, SearchCategory]:
        extractor_message = FacadeMainExtractorMessage(
            env=env, session_id=session_id, uri=uri, prompts=prompts, min_box=min_box, rmbg=rmbg
        )
        extracted = await ExtractorService.do_extract(extractor_message)
        if not extracted.is_success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'{extracted.error_code} | {extracted.error_message}'
            )

        if not run_searchers:
            return extracted, SearchCategory()

        faiss_category = await SearcherService.search_milvus(extracted)
        if faiss_category is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Searcher is unavailable'
            )

        return extracted, faiss_category

    @staticmethod
    async def cloud_execution_lens(storage, bucket, path, domains) -> tuple[dict, dict, list]:
        signed_url = storage.sign_url(bucket, path)
        lens_dto, keywords = await LENS_HELPER.exec_lens(signed_url, domains)
        custom_search_dto = await exec_custom_search(keywords, domains)
        return lens_dto, custom_search_dto, keywords

    @staticmethod
    async def cloud_execution_vision(storage, bucket, path, domains) -> tuple[dict, list]:
        if storage == CloudStorage.S3:
            uri = storage.sign_url(bucket, path)
        else:
            uri = CloudStorage.GCS.to_uri(bucket, path)
        _, _, keywords = await VisionHelper.exec_vision(uri)
        custom_search_dto = await exec_custom_search(keywords, domains)
        return custom_search_dto, keywords


class ExtractorService:
    last_wake_up_time = 0

    @staticmethod
    def wake_up_extractors_non_blocking():
        current_time = time.time()
        if current_time - ExtractorService.last_wake_up_time < 1:
            return

        ExtractorService.last_wake_up_time = current_time
        for url in get_settings().extractor_urls:
            asyncio.create_task(HttpAsyncBuilder(url=f'{url}/wake').execute())

    @staticmethod
    async def do_extract(extractor_message: ExtractorMessage) -> ExtractorResponse:
        success = AwsService.send_to_sqs(extractor_message)
        if not success:
            return ExtractorResponse(
                env=extractor_message.env,
                session_id=extractor_message.session_id,
                uri=extractor_message.uri,
                error_code='SQS_SEND_ERROR',
                error_message='Failed to send message to SQS'
            )

        try:
            return await AwsService.poll_extractor_result_from_redis(extractor_message)
        except RedisPollError as e:
            if extractor_message.is_critical:
                log_exception(
                    f'{e.code.value} | Critical | {extractor_message.env} | {extractor_message.uri}',
                    logger.error
                )
            else:
                log_exception(
                    f'{e.code.value} | NonCritical | {extractor_message.env} | {extractor_message.uri}',
                    logger.warning
                )
            return ExtractorResponse(
                env=extractor_message.env,
                session_id=extractor_message.session_id,
                uri=extractor_message.uri,
                error_code=e.code.value
            )


class SearcherService:
    @staticmethod
    async def search_milvus(extracted: ExtractorResponse) -> SearchCategory | None:
        searcher_dict = get_searcher_dict()
        results = await SearcherService._do_search_milvus(extracted, searcher_dict)

        result_datasets = []
        for item in results:
            dataset = SearchDataset(
                dataset=item['dataset'],
                size=item['size'],
                feature_position=item['idx'],
                display_name=searcher_dict[item['col']]['displayName'],
                thumbnail_dir_uri=searcher_dict[item['col']]['thumbnailDirUri']
            )
            for arr in item['vectors']:
                for v in arr:
                    score = 0.5 * (1 + v['distance'])
                    vector = SearcherVector(vid=v['id'], score=score)
                    dataset.vectors.append(vector)
            result_datasets.append(dataset)

        search_resp = SearcherResponse(search_datasets=result_datasets)
        category = await SearcherService._uniform_search_categories(search_resp)
        return category

    @staticmethod
    @timed_plus(tag='SearchMilvus', level_func=logger.debug)
    async def _do_search_milvus(extracted, searcher_dict):
        tasks = []
        for idx, ext_dto in enumerate(extracted.extraction):
            for item in searcher_dict.values():
                if idx == 0 and item['col'].endswith('box'):
                    continue
                elif idx >= 1 and not item['col'].endswith('box'):
                    continue
                else:
                    tasks.append(asyncio.to_thread(
                        SearcherService._create_search_task,
                        item=item,
                        idx=idx,
                        features=ext_dto.features
                    ))
        return await asyncio.gather(*tasks)

    @staticmethod
    def _create_search_task(item: dict, idx: int, features: list[float]) -> dict:
        try:
            vectors = MilvusClient(uri=item['searcherUrl']).search(
                collection_name=item['col'],
                anns_field='feature',
                search_params={'metric_type': 'IP', 'params': {'nprobe': 64}},
                limit=20,
                data=[features]
            )
        except Exception as e:
            log_exception(f'MilvusESearcherErr | {item['col']}')
            vectors = []

        return {
            'idx': idx,
            'col': item['col'],
            'dataset': item['dataset'],
            'size': item['size'],
            'vectors': vectors
        }

    @staticmethod
    @timed_plus(tag='SearchInfoDb', level_func=logger.debug)
    async def _uniform_search_categories(searcher_resp: SearcherResponse):
        faiss_category = SearchCategory(omissions=searcher_resp.omissions)

        tasks = []
        for ss in searcher_resp.search_datasets:
            task = asyncio.create_task(SearcherService._create_dataset_query_task(ss))
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        for result in results:
            faiss_category.matches.append(result)

        return faiss_category

    @staticmethod
    async def _create_dataset_query_task(search_dataset: SearchDataset):
        await MongoService.query_dataset_vectors(search_dataset)
        return CategoryMatch(
            key=search_dataset.dataset,
            name=search_dataset.display_name,
            category='faiss',
            items=[RankItem(**vv.to_rank_item_dict()) for vv in search_dataset.vectors],
            extra={'size': search_dataset.size}
        )
