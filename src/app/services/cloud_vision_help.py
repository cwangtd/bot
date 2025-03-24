import json

from google.cloud import vision_v1
from google.protobuf.json_format import MessageToDict

from app.common.logger_common import logger


class VisionHelper:
    @staticmethod
    async def exec_vision(img_uri) -> tuple[dict, dict, list]:
        image = vision_v1.Image()
        image.source.image_uri = img_uri

        request = vision_v1.AnnotateImageRequest(
            image=image,
            features=[
                vision_v1.Feature(type=vision_v1.Feature.Type.LOGO_DETECTION),
                vision_v1.Feature(type=vision_v1.Feature.Type.WEB_DETECTION),
            ]
        )

        resp = await vision_v1.ImageAnnotatorAsyncClient().batch_annotate_images(requests=[request])
        item = [MessageToDict(item) for item in resp.responses.pb][0]

        logger.debug(f'Vision | {img_uri} | {json.dumps(item)}')

        logo = item.get('logoAnnotations', {})
        web = item.get('webDetection', {})
        keywords = []
        if 'description' in logo:
            keywords.append(logo['description'])
        if 'bestGuessLabels' in web:
            for label in web['bestGuessLabels']:
                keywords.append(label['label'])

        return logo, web, keywords
