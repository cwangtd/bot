import asyncio

from app.common.logger_common import log_exception, logger
from app.models.dto import SearchCategory, RankItem, CategoryMatch, CloudItemExtractorMessage
from app.models.dto_v3 import ExtractorResponse
from app.services.facade_service import ExtractorService
from app.utils import calc_score, convert_to_omission
from app.utils.verify_facebook import is_whitelist_facebook_item
from app.utils.verify_instagram import is_whitelist_instagram_item
from app.utils.verify_tiktok import is_whitelist_tiktok_item
from app.utils.verify_twitter import is_whitelist_twitter_item
from app.utils.verify_youtube import batch_verify_youtube, is_youtube_source_or_hostname, parse_youtube_video_id


class CloudService:
    @staticmethod
    async def conclude_cloud(
            features: list[float],
            lens: dict,
            custom_search: dict,
            env: str,
            session_id: str,
            cap: int
    ) -> SearchCategory:
        lens_categories = None
        custom_search_categories = None

        try:
            await CloudService.conclude_social_media_official_accounts(lens, custom_search)
            distributed_items = CloudService.distribute_items(lens, custom_search, cap)

            if len(distributed_items) == 0:
                return SearchCategory()

            img_urls = [item['imageUrl'] for item in distributed_items]

            task_responses = await asyncio.gather(
                *[
                    ExtractorService.do_extract(
                        extractor_message=CloudItemExtractorMessage(
                            env=env, session_id=session_id, uri=img_url, serial=one_based_serial
                        )
                    )
                    for one_based_serial, img_url in enumerate(img_urls, start=1)
                ]
            )
            url_extraction_dict = {tr.uri: tr for tr in task_responses}
            un_extractable_urls = CloudService.update_match_items(features, distributed_items, url_extraction_dict)

            CloudService.filter_urls(un_extractable_urls, lens['matches'], lens['omissions'])
            CloudService.filter_urls(un_extractable_urls, custom_search['matches'], custom_search['omissions'])

            [items['items'].sort(key=lambda x: x['score'], reverse=True) for items in custom_search['matches']]
            [items['items'].sort(key=lambda x: x['score'], reverse=True) for items in lens['matches']]

            lens_categories = CloudService.uniform_category(lens, 'lens')
            custom_search_categories = CloudService.uniform_category(custom_search, 'custom-search')

        except Exception:
            log_exception('LensConclusion')

        if custom_search_categories is not None and lens_categories is not None:
            joined = SearchCategory(
                matches=lens_categories.matches + custom_search_categories.matches,
                omissions=lens_categories.omissions + custom_search_categories.omissions
            )
        elif lens_categories is not None:
            joined = lens_categories
        elif custom_search_categories is not None:
            joined = custom_search_categories
        else:
            joined = SearchCategory()

        joined.deduplicate_by_img_url()
        joined.sort_matches_by_score()
        return joined

    @staticmethod
    def distribute_items(lens: dict, custom_search: dict, cap: int) -> list[dict]:
        match_lists = lens.get('matches', []) + custom_search.get('matches', [])
        max_len = max((len(ml['items']) for ml in match_lists), default=0)

        flatten_items = []
        lens_cut_at = 0
        custom_search_cut_at = 0  # custom_search_cut_at could be 1 less than lens_cut_at

        for i in range(max_len):
            for lens_match_items in lens['matches']:
                if i < len(lens_match_items['items']):
                    flatten_items.append(lens_match_items['items'][i])
            lens_cut_at = i + 1
            # If cap is reached and have at least one custom_search item, stop.
            if len(flatten_items) >= cap and custom_search_cut_at > 0:
                break

            for custom_search_match_items in custom_search['matches']:
                if i < len(custom_search_match_items['items']):
                    flatten_items.append(custom_search_match_items['items'][i])
            custom_search_cut_at = i + 1
            if len(flatten_items) >= cap:
                break

        CloudService.cut_matches_to_omissions(lens, lens_cut_at)
        CloudService.cut_matches_to_omissions(custom_search, custom_search_cut_at)

        return flatten_items

    @staticmethod
    def cut_matches_to_omissions(category, cut_at):
        for matches in category['matches']:
            if cut_at >= len(matches['items']):
                continue
            for item in matches['items'][cut_at:]:
                item['by'] = 'softCap'
            category['omissions'].extend(matches['items'][cut_at:])
            matches['items'] = matches['items'][:cut_at]

    @staticmethod
    def uniform_category(input_dict, category) -> SearchCategory:
        search_category = SearchCategory(omissions=[
            {**item, 'category': category} for item in input_dict['omissions']
        ])
        for mm in input_dict['matches']:
            key_match = CategoryMatch(key=mm['key'], name=mm['key'], category=category)
            key_match.items.extend(
                RankItem(
                    title=ii['title'],
                    score=ii['score'],
                    thumbnail_uri=ii['thumbnailUri'],
                    extra={k: ii[k] for k in ['source', 'pageUrl', 'imageUrl']}
                ) for ii in mm['items']
            )
            search_category.matches.append(key_match)
        return search_category

    @staticmethod
    async def conclude_social_media_official_accounts(lens, custom_search):
        try:
            youtube_items = {}
            filtered1, total1 = CloudService.filter_by_url_parsing(
                lens, lens['matches'], lens['omissions'], youtube_items
            )
            filtered2, total2 = CloudService.filter_by_url_parsing(
                custom_search, custom_search['matches'], custom_search['omissions'], youtube_items
            )
            logger.debug(f'SocialFilter | {filtered1}/{total1} | {filtered2}/{total2}')

            if len(youtube_items) > 0:
                youtube_results = await batch_verify_youtube(list(youtube_items.keys()))
                for video_id, is_official_account in youtube_results.items():
                    if not is_official_account:
                        for src_dict, match, item in youtube_items[video_id]:
                            src_dict['omissions'].append(convert_to_omission(item))
                            match['items'].remove(item)

            lens['matches'] = [match for match in lens['matches'] if len(match['items']) > 0]
            custom_search['matches'] = [match for match in custom_search['matches'] if len(match['items']) > 0]

        except Exception:
            log_exception('SocialMediaOfficialAccounts')

    @staticmethod
    def update_match_items(
            features1: list[float],
            flatten_items,
            url_extraction_dict: dict[str, ExtractorResponse]
    ):
        un_extractable_urls = []
        for item in flatten_items:
            item['score'] = -1.0
            item['thumbnailUri'] = ''
            if item['imageUrl'] in url_extraction_dict:
                extractor_resp: ExtractorResponse = url_extraction_dict[item['imageUrl']]
                if extractor_resp.is_success:
                    features2 = extractor_resp.extraction[0].features
                    score = calc_score(features1, features2)
                    item['score'] = score
                    item['thumbnailUri'] = extractor_resp.thumbnail_uri
                else:
                    un_extractable_urls.append(item['imageUrl'])
            else:
                un_extractable_urls.append(item['imageUrl'])
        return un_extractable_urls

    @staticmethod
    def filter_urls(
            un_extractable_urls: list[str],
            matches: list[dict],
            omissions: list[dict]
    ):
        for match in matches:
            keepers = []
            for item in match['items']:
                if item['imageUrl'] in un_extractable_urls:
                    omissions.append(convert_to_omission(item))
                else:
                    keepers.append(item)
            match['items'] = keepers

    @staticmethod
    def filter_by_url_parsing(
            src_root_dict: dict, src_matches: list, src_omissions: list, youtube_items: dict
    ) -> tuple[int, int]:
        total = 0
        omissions = []
        for match in src_matches:
            for item in match['items']:
                CloudService.filtering(item, match, omissions, src_root_dict, youtube_items)
                total += 1

        for match, item in omissions:
            src_omissions.append(convert_to_omission(item))
            match['items'].remove(item)

        return total - len(omissions), total

    @staticmethod
    def filtering(item, match, omissions, src_root_dict, youtube_items):
        if is_youtube_source_or_hostname(item['source'], item['pageUrl']):
            video_id = parse_youtube_video_id(item['pageUrl'])
            if video_id is None:
                omissions.append(tuple((match, item)))
            elif video_id in youtube_items:
                youtube_items[video_id].append((src_root_dict, match, item))
            else:
                youtube_items[video_id] = [(src_root_dict, match, item)]

        elif is_whitelist_facebook_item(item['source'], item['pageUrl']) is False:
            omissions.append(tuple((match, item)))

        elif is_whitelist_instagram_item(item['source'], item['pageUrl']) is False:
            omissions.append(tuple((match, item)))

        elif is_whitelist_twitter_item(item['source'], item['pageUrl']) is False:
            omissions.append(tuple((match, item)))

        elif is_whitelist_tiktok_item(item['source'], item['pageUrl']) is False:
            omissions.append(tuple((match, item)))
