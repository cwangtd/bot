from urllib.parse import urlparse

from fastapi import APIRouter, Query, HTTPException
from pymongo import AsyncMongoClient
from starlette import status
from starlette.responses import JSONResponse

from app import get_settings, AppConst
from app.models.shooter_dto import ShooterDto
from app.services.shooter_controller import ShooterController
from app.storage.storage_utils import CloudStorage

router_internal = APIRouter()


@router_internal.get(path='/sign', response_class=JSONResponse)
async def exec_session(
        uri: str
) -> dict:
    return {'url': CloudStorage.sign_uri(uri)}


@router_internal.get(path='/shooter/{env}/{response_id}', response_class=JSONResponse)
async def exec_session(
        env: str, response_id: str
) -> ShooterDto:
    return await ShooterController(env, response_id).execute()


@router_internal.get(path='/locator', response_class=JSONResponse)
async def exec_locator(
        url: str = Query(description='Signed GCP image URL from Provenance/AIGC')
) -> dict:
    parsed = urlparse(url)
    segments = parsed.path.split('/')
    if not parsed.scheme or len(segments) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid URL: {url}'
        )

    env = segments[2]
    generation_id = segments[4]
    supported_env = [x for x in AppConst.ENVS if x.startswith('provenance')]
    if env not in supported_env:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Supported env: {supported_env}'
        )

    db = get_aigc_portal_db(env)
    col = 'prAIGCCCheckRequest'
    doc = await db[col].find_one({'generationRequestId': generation_id})

    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Failed to find doc: env={env}, generation_id={generation_id}'
        )

    return {
        'env': env,
        'responseId': doc['facadeResultV3']['responseId'],
        'key': f'{env}/{generation_id}'
    }


def get_aigc_portal_db(env: str):
    mongodb_uri = get_settings().api_db_uri
    try:
        client = AsyncMongoClient(mongodb_uri)
        return client[f'aigc-{env.replace('.', '-')}']
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to connect to AIGC Portal DB: {mongodb_uri}'
        )
