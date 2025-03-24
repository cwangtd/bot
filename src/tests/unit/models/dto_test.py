import pytest
from pydantic import ValidationError

from app.models.dto import CloudItemExtractorMessage, FacadeMainExtractorMessage


def test_cloud_item_extractor_message_serial():
    msg = CloudItemExtractorMessage(env='prod', session_id='123', uri='some/uri', serial=1)
    assert msg.serial == 1

    with pytest.raises(ValidationError) as e:
        CloudItemExtractorMessage(env='prod', session_id='123', uri='some/uri', serial=0)

    assert 'Input should be greater than or equal to 1' in str(e.value)


def test_is_critical():
    facade_main_extractor_message = FacadeMainExtractorMessage(
        env='prod', session_id='123', uri='some/uri', prompts='', min_box=0, rmbg=False
    )
    assert facade_main_extractor_message.is_critical

    cloud_item_extractor_message = CloudItemExtractorMessage(
        env='prod', session_id='123', uri='some/uri', serial=1
    )
    assert not cloud_item_extractor_message.is_critical
