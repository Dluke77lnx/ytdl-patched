# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import (
    try_get,
    ExtractorError,
)
from ..compat import (
    compat_str,
)


class WhoWatchIE(InfoExtractor):
    IE_NAME = 'whowatch'
    _VALID_URL = r'https?://whowatch\.tv/viewer/(?P<id>\d+)/?'
    META_API_URL = 'https://api.whowatch.tv/lives/%s'
    LIVE_API_URL = 'https://api.whowatch.tv/lives/%s/play'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        self._download_webpage(url, video_id)
        metadata = self._download_json(self.META_API_URL % video_id, video_id)
        live_data = self._download_json(self.LIVE_API_URL % video_id, video_id)

        title = try_get(None, (
            lambda x: live_data['share_info']['live_title'][1:-1],
            lambda x: metadata['live']['title'],
        ), compat_str)

        hls_url = live_data.get('hls_url')
        if not hls_url:
            raise ExtractorError(live_data.get('error_message') or 'The live is offline.', expected=True)

        formats = []
        streams = live_data.get('streams') or []

        formats.extend(self._extract_m3u8_formats(
            hls_url, video_id, ext='mp4', entry_protocol='m3u8_native',
            m3u8_id='root', preference=len(streams) * 2))

        for i, fmt in enumerate(streams):
            name = fmt.get('name') or 'source-%d' % i
            rtmp_url = fmt.get('rtmp_url')
            if not rtmp_url:
                continue
            formats.append({
                'url': rtmp_url,
                'format_id': '%s-rtmp' % name,
                'ext': 'mp4',
                'protocol': 'rtmp',
                'preference': len(streams) - i,
                'vcodec': 'none' if fmt.get('audio_only') else None,
            })

        self._sort_formats(formats)

        uploader_id = try_get(metadata, lambda x: x['live']['user']['user_path'], compat_str)
        uploader_id_internal = try_get(metadata, lambda x: x['live']['user']['id'], int)
        uploader = try_get(metadata, lambda x: x['live']['user']['name'], compat_str)

        return {
            'id': video_id,
            'title': title,
            'uploader_id': uploader_id,
            'uploader_id_internal': uploader_id_internal,
            'uploader': uploader,
            'formats': formats,
            'is_live': True,
        }
