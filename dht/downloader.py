#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-13


class Downloader(object):
    @classmethod
    def download_from_third_cache(cls, info_hash):
        # upper_hash = info_hash.upper()
        pass

    @classmethod
    def __url_from_xunlei(cls, info_hash):
        return 'http://bt.box.n0808.com/%s/%s/%s.torrent' % (info_hash[:2], info_hash[-3:-1], info_hash)

    @classmethod
    def __url_from_vuze(cls, info_hash):
        return 'http://magnet.vuze.com/magnetLookup?hash=' + info_hash

    @classmethod
    def __url_from_torrage(cls, info_hash):
        return 'http://torrage.com/torrent/%s.torrent' % info_hash

    @classmethod
    def __url_from_torcache(cls, info_hash):
        # see other http://torrage.info
        return 'http://torrage.info/torrent.php?h=%s' % info_hash

    @classmethod
    def __url_from_zoink(cls, info_hash):
        return 'http://zoink.it/torrent/%s.torrent' % info_hash
