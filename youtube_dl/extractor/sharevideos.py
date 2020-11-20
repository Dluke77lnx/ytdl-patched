# coding: utf-8
from __future__ import unicode_literals

from ..utils import KNOWN_EXTENSIONS, determine_ext, mimetype2ext, try_get
from .common import InfoExtractor


class ShareVideosIE(InfoExtractor):
    IE_NAME = 'sharevideos'
    _VALID_URL = r'https?://(?:embed\.)?share-videos\.se/auto/(?:embed|video)/(?P<id>\d+)\?uid=(?P<uid>\d+)'
    TEST = {
        'url': 'http://share-videos.se/auto/video/83645793?uid=13',
        'md5': 'b68d276de422ab07ee1d49388103f457',
        'info_dict': {
            'id': '83645793',
            'title': 'Lock up and get excited',
            'ext': 'mp4'
        },
        'skip': 'TODO: fix nested playlists processing in tests',
    }

    def _real_extract(self, url):
        video_id = self._match_id(url)
        uid = self._VALID_URL_RE.match(url).group('uid')
        webpage = self._download_webpage('https://embed.share-videos.se/auto/embed/%s?uid=%s' % (video_id, uid), video_id)

        title = self._html_extract_title(webpage, 'video title', default=None)
        if not title:
            video_webpage = self._download_webpage(
                'https://share-videos.se/auto/video/%s?uid=%s' % (video_id, uid),
                video_id)
            title = self._html_extract_title(video_webpage, 'video title', default=None)
        if not title:
            tags = self._download_json(
                'https://search.share-videos.se/json/movie_tag?svid=%s&site=sv' % video_id,
                video_id, note='Giving it a better name', fatal=None)
            if tags and isinstance(tags, (list, tuple)):
                title = ' '.join(tags)
        if not title:
            self.report_warning('There is no title candidate for this video', video_id)
            title = 'untitled'

        def extract_mp4_url(x):
            src = self._search_regex(r'random_file\.push\("(.+)"\);', webpage, 'video url')
            src_type = self._search_regex(r'player.src\({type: \'(.+);\',', webpage, 'video type', fatal=False, default='video/mp4')
            ext = determine_ext(src).lower()
            return {
                'formats': [
                    {
                        'url': src,
                        'ext': (mimetype2ext(src_type)
                                or ext if ext in KNOWN_EXTENSIONS else 'mp4'),
                    }
                ]
            }
        entry = try_get(webpage, (
            lambda x: self._parse_html5_media_entries(url, webpage, video_id, m3u8_id='hls')[0],
            extract_mp4_url,
        ), dict)
        self._sort_formats(entry['formats'])
        entry.update({
            'id': video_id,
            'title': title,
        })
        return entry
