from fastapi import HTTPException
from starlette import status

from app import get_searcher_dict
from app.common.logger_common import log_exception
from app.models.dto import CategoryMatch
from app.models.shooter_dto import ShooterStatus, ShooterDto
from app.services.mongo_service import MongoService
from app.services.ranker_controller import MatchRanker


class ShooterController:
    def __init__(self, env: str, response_id: str):
        self.env = env
        self.response_id = response_id

    async def execute(self) -> ShooterDto:
        doc = await MongoService.find_facade_doc(self.env, self.response_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f'Failed to find doc: env={self.env}, response_id={self.response_id}'
            )

        search_dict = get_searcher_dict()
        try:
            doc_matches = doc.get('matches', [])
            for match in doc_matches:
                col_name = match['key'].replace('-', '_')
                if match.get('category', '') == 'faiss' and col_name in search_dict:
                    match['name'] = search_dict[col_name]['displayName']
            matches = [CategoryMatch(**match) for match in doc_matches]
        except Exception as e:
            log_exception('Shooter')
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing matches: env={self.env}, response_id={self.response_id}"
            )

        request_id = doc.get('input', {}).get('reqId', '')
        ranks = MatchRanker.ranks_000(matches)
        dto = MatchRanker.compose_standard_result(request_id, self.response_id, ranks)

        dur_len = len(doc['_dur'])
        if 'error' in doc:
            dto.status = ShooterStatus.ERROR
        elif dur_len == 0:
            dto.status = ShooterStatus.PENDING
        elif dur_len == 1:
            dto.status = ShooterStatus.STAGE1
        else:
            dto.status = ShooterStatus.COMPLETE

        return dto
