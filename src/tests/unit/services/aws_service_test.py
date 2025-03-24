from unittest.mock import patch, MagicMock

import pytest

from app.exceptions.RedisPollError import RedisPollError
from app.models.dto import CloudItemExtractorMessage
from app.services.aws_service import AwsService


@pytest.mark.asyncio
@patch.object(AwsService, 'redis_client')
async def test_poll_success(mock_redis_client):
    mock_redis_client.return_value = MagicMock()
    AwsService.redis_client.get.return_value = '''
{
  "env": "provenance.local.dev",
  "session_id": "f7e5180d-4738-4f86-b1b4-10a6bded16c2",
  "uri": "s3://alamy-data/0001/2A000A2.jpg",
  "min_box": 0.25,
  "box_prompts": "cartoon character",
  "rmbg": false,
  "extraction": [
    {
      "score": -1,
      "ratio": 1,
      "boxes": [
        0,
        0,
        4200,
        2913
      ],
      "features": [
        0, 0
      ]
    }
  ],
  "image_uri": "",
  "thumbnail_uri": "",
  "http_status": 200,
  "error_code": "",
  "error_message": ""
}    
'''
    result = await AwsService.poll_extractor_result_from_redis(
        CloudItemExtractorMessage(env='env', session_id='session_id', uri='uri', serial=1)
    )
    assert result.is_success


@pytest.mark.asyncio
@patch.object(AwsService, 'redis_client')
async def test_poll_error(mock_redis_client):
    mock_redis_client.return_value = MagicMock()
    AwsService.redis_client.get.return_value = 'not json'
    with pytest.raises(RedisPollError, match='Code.DECODE'):
        await AwsService.poll_extractor_result_from_redis(
            CloudItemExtractorMessage(env='env', session_id='session_id', uri='uri', serial=1)
        )


@pytest.mark.asyncio
@patch.object(AwsService, 'redis_client')
async def test_poll_timeout(mock_redis_client):
    mock_redis_client.return_value = MagicMock()
    AwsService.redis_client.get.return_value = None
    with pytest.raises(RedisPollError, match='Code.TIMEOUT'):
        await AwsService.poll_extractor_result_from_redis(
            CloudItemExtractorMessage(env='env', session_id='session_id', uri='uri', serial=1), timeout=1
        )
