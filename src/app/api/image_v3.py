from functools import wraps

from fastapi import APIRouter, Path, Query, HTTPException
from starlette import status
from starlette.responses import JSONResponse

from app import AppConst
from app.models.shooter_dto import ShooterDto
from app.services.facade_controller import FacadeController, Mode, Stage
from app.services.shooter_controller import ShooterController
from app.storage.storage_utils import CloudStorage

router_v3 = APIRouter()

DEFAULT_BOX_PROMPTS = AppConst.DEFAULT_BOX_PROMPTS
DEFAULT_MIN_BOX_DETECT_RATIO = AppConst.DEFAULT_MIN_BOX_DETECT_RATIO
DEFAULT_BACKGROUND_REMOVAL = AppConst.DEFAULT_BACKGROUND_REMOVAL


def transform_str_to_enum(kwargs: dict, key: str, enum_cls):
    if isinstance(kwargs[key], enum_cls):
        return

    if not isinstance(kwargs[key], str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Invalid type of {key}: {type(kwargs[key])}'
        )

    try:
        kwargs[key] = enum_cls[kwargs[key].upper()]
    except (KeyError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Supported {key}: {enum_cls}'
        )


def param_validator(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        validate_storage(kwargs)
        validate_env(kwargs)
        validate_mode(kwargs)
        validate_stage(kwargs)
        return await func(*args, **kwargs)

    def validate_storage(kwargs):
        if 'storage' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Required: storage'
            )
        transform_str_to_enum(kwargs, 'storage', CloudStorage)

    def validate_env(kwargs):
        if 'env' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Required: env'
            )
        if kwargs['env'] not in AppConst.ENVS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Supported env: {AppConst.ENVS}'
            )

    def validate_mode(kwargs):
        if 'mode' in kwargs:
            transform_str_to_enum(kwargs, 'mode', Mode)

    def validate_stage(kwargs):
        if kwargs['env'].startswith('c-check.external.api'):
            kwargs['stage'] = Stage.TWO
        elif 'stage' in kwargs:
            transform_str_to_enum(kwargs, 'stage', Stage)
        else:
            kwargs['stage'] = Stage.SINGLE

    return wrapper


@router_v3.get(path='/image/{storage}/{bucket}/{path:path}', response_class=JSONResponse)
@param_validator
async def exec_image(
        # path params
        storage: str | CloudStorage,
        bucket: str,
        path: str = Path(...),
        # session query params
        env: str = Query(
            default='',
            description='Required session param, the target Provenance environment'
        ),
        request_id: str = Query(
            default='',
            description='Optional session param, the optional request ID'
        ),

        # flow control query params
        mode: str | Mode = Query(
            default=Mode.FULL,
            description='Optional flow control param, full (default) | facade | lens'
        ),
        stage: str | Stage = Query(
            default=Stage.SINGLE,
            description='Optional flow control param, full (default) | one'
        ),

        # extractor query params
        prompts: str = Query(
            default=DEFAULT_BOX_PROMPTS,
            description='Optional extractor param, prompts for box detection'
        ),
        min_box: float = Query(
            default=DEFAULT_MIN_BOX_DETECT_RATIO,
            description='Optional extractor param, the minimum bounding box ratio to the image'
        ),
        rmbg: bool = Query(
            default=DEFAULT_BACKGROUND_REMOVAL,
            description='Optional extractor param, the flag of background removal'
        ),
):
    return await FacadeController(
        storage=storage,
        bucket=bucket,
        path=path,
        env=env,
        request_id=request_id
    ).execute_flow(
        mode=mode,
        stage=stage,
        min_box=min_box,
        prompts=prompts,
        rmbg=rmbg
    )


@router_v3.get(path='/session/{env}/{response_id}', response_class=JSONResponse)
async def exec_session(
        env: str, response_id: str
) -> ShooterDto:
    return await ShooterController(env, response_id).execute()


@router_v3.get(path='/image/info', response_class=JSONResponse)
async def get_domains() -> dict:
    return {
        'envs': AppConst.ENVS,
        'domains': AppConst.DOMAINS,
        'subsidiaryDomains': AppConst.SUB_DOMAINS
    }
