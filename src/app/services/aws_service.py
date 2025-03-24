import asyncio
import json

from app.common.logger_common import log_exception, logger, to_elapsed_seconds
from app.exceptions.RedisPollError import RedisPollError
from app.models.dto import ExtractorMessage
from app.models.dto_v3 import ExtractorResponse
from app.utils.lrucache import get_settings, get_aws_sqs_client, get_aws_redis_client


class AwsService:
    redis_client = get_aws_redis_client()

    @staticmethod
    def send_to_sqs(message: ExtractorMessage) -> bool:
        _json = message.model_dump_json()
        try:
            queue_url = get_settings().get_sqs_url(message.is_critical)
            response = get_aws_sqs_client().send_message(
                QueueUrl=queue_url,
                MessageBody=_json
            )
            logger.debug(f'SqsSent | {response}')
            return True

        except Exception as e:
            log_exception(f'SqsSend | {message.env} | {message.uri}')
            return False

    @staticmethod
    async def poll_extractor_result_from_redis(
            dto: ExtractorMessage, timeout: int = 30, interval: int = 1
    ) -> ExtractorResponse:
        loop = asyncio.get_running_loop()
        start_ts = loop.time()

        while True:
            try:
                value = await AwsService.redis_client.get(dto.key)
            except Exception as e:
                log_exception(f'{RedisPollError.Code.GET.value} | {dto.key}')
                raise RedisPollError(RedisPollError.Code.GET)

            if value is not None:
                try:
                    _dict = json.loads(value)
                    logger.debug(f'RedisPolled | {dto.key} | {to_elapsed_seconds(loop.time() - start_ts)}')
                    await AwsService.redis_client.delete(dto.key)
                    return ExtractorResponse(**_dict)
                except json.JSONDecodeError:
                    log_exception(f'{RedisPollError.Code.DECODE.value} | {dto.key} | {value}')
                    raise RedisPollError(RedisPollError.Code.DECODE)

            elapsed = loop.time() - start_ts
            if elapsed >= timeout:
                log_exception(f'{RedisPollError.Code.TIMEOUT.value} | {dto.key} | {to_elapsed_seconds(elapsed)}')
                raise RedisPollError(RedisPollError.Code.TIMEOUT)

            await asyncio.sleep(interval)
