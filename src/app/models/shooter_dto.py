from enum import Enum

from fastapi_camelcase import CamelModel


class ShooterStatus(Enum):
    ERROR = 'ERROR'
    PENDING = 'PENDING'
    STAGE1 = 'STAGE1'
    COMPLETE = 'COMPLETE'


class ShooterDto(CamelModel):
    request_id: str
    response_id: str
    status: ShooterStatus = ShooterStatus.PENDING
    ranks: list[dict] = []
    rankVer: str = '000'
