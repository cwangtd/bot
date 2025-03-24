import json
import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    stage: str = ''
    workspace: str = '/opt'  # from global environment variable

    log_level: str = 'INFO'
    log_format: str = '%(levelname)s %(name)s %(thread)d | %(message)s'  # for cloudwatch
    log_path: str = ''
    log_in_json: bool = False

    info_db_uri: str = 'mongodb+srv://provenance:uBIOW17cuTrDdMnT@provenance.p5pyz.mongodb.net/c-check-provenance?retryWrites=true&w=majority&appName=Provenance'
    api_db_uri: str = ''

    extractor_ips: str = ''
    # baseline: http://10.120.143.67:19530
    # wikimedia: http://10.120.138.67:19530
    # alamy: http://10.120.129.158:19530
    # NOTE: the first one must be baseline
    milvus_uris_str: str = 'http://10.120.143.67:19530,http://10.120.138.67:19530,http://10.120.129.158:19530'

    aws_sqs_queue_region: str = 'us-east-1'

    aws_redis_host: str = ''
    aws_redis_port: int = 6379

    model_config = SettingsConfigDict(
        env_file='/opt/.env',
        env_file_encoding='utf-8',
        extra='allow'
    )

    @property
    def res_path(self):
        return f'{self.workspace}/app/resources'

    @property
    def extractor_urls(self) -> list[str]:
        return [f'http://{x}:8003' for x in self.extractor_ips.split(';;')]

    @property
    def milvus_uris(self) -> list[str]:
        return self.milvus_uris_str.split(',') if self.milvus_uris_str else []

    @property
    def gcp_secret_path(self) -> str:
        path = f'{self.res_path}/secrets/gcp-secret.json'
        if not os.path.exists(path):
            raise SystemExit(f'gcp secret file not exist: {path}')
        return path

    @property
    def aws_secret_json(self) -> dict:
        path = f'{self.res_path}/secrets/aws-secret.json'
        if not os.path.exists(path):
            raise SystemExit(f"aws secret file not exist: {path}")

        with open(path, 'r') as f:
            return json.load(f)

    def get_sqs_url(self, is_critical: bool) -> str:
        _priority = 'critical' if is_critical else 'regular'
        _stage = self.stage if self.stage == 'prod' else 'dev'
        return f'https://sqs.us-east-1.amazonaws.com/572111738119/c-extractor-{_priority}-{_stage}'
