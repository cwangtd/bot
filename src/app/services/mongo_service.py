import logging

from app import get_info_db, get_api_db, get_settings
from app.models.dto_v3 import SearchDataset

logger = logging.getLogger('main.app')


class MongoService:
    @staticmethod
    async def query_dataset_vectors(dataset: SearchDataset):
        info_col_name = dataset.col_name
        field = 'int20id' if info_col_name == 'video' else 'int64id'
        query_ids = [v.query_field for v in dataset.vectors]

        docs = await get_info_db()[info_col_name].find({field: {'$in': list(query_ids)}}).to_list()
        title_dict = {
            doc[field]: doc['title']
            for doc in docs if 'title' in doc
        }
        for doc in docs:
            if 'title' not in doc:
                logging.warning(f"Excluded | {info_col_name} | {doc}")

        missing_field_values = []
        for vv in dataset.vectors:
            field_value = vv.query_field
            if field_value in title_dict:
                vv.title = title_dict[field_value]
            else:
                missing_field_values.append(field_value)

        if missing_field_values:
            logger.warning(f'Missing | {info_col_name} | {field} | {missing_field_values}')

    @staticmethod
    def get_api_col(env: str) -> str:
        _env = env.lower().replace('-', '_').replace('.', '_')
        return f'facade_{_env}'

    @staticmethod
    async def insert_facade_doc(env: str, doc: dict):
        db = get_api_db()
        col = MongoService.get_api_col(env)
        result = await db[col].insert_one(doc)
        logger.debug(f'FacadeDoc | {db.name}.{col} | {result.inserted_id} | {get_settings().api_db_uri}')

    @staticmethod
    async def update_facade_doc(env: str, doc: dict, session_id: str):
        db = get_api_db()
        col = MongoService.get_api_col(env)
        result = await db[col].update_one({'_id': session_id}, {'$set': doc})
        logger.debug(f'UpdateDoc | {db.name}.{col} | {result.upserted_id} | {get_settings().api_db_uri}')

    @staticmethod
    async def find_facade_doc(env: str, session_id: str) -> dict:
        db = get_api_db()
        col = MongoService.get_api_col(env)
        logger.debug(f'QueryDoc | {db.name}.{col} | {session_id} | {get_settings().api_db_uri}')
        return await db[col].find_one({'_id': session_id})
