#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-27

import time
# import hashlib
import bencode


class Parser(object):
    @classmethod
    def parse_torrent(cls, data):
        torrent = data
        if not isinstance(torrent, dict):
            try:
                torrent = bencode.bdecode(torrent)
            except:
                return None
        info = {}
        try:
            info['create_time'] = int(torrent['creation date'])
        except:
            info['create_time'] = int(time.time())

        encoding = torrent.get('encoding', 'utf8')
        if torrent.get('announce'):
            info['announce'] = cls.__decode_utf8(encoding, torrent, 'announce')

        # if 'comment' in torrent:
        #     info['comment'] = cls.__decode_utf8(encoding, torrent, 'comment')[:200]
        # if 'publisher-url' in torrent:
        #     info['publisher-url'] = cls.__decode_utf8(encoding, torrent, 'publisher-url')
        # if 'publisher' in torrent:
        #     info['publisher'] = cls.__decode_utf8(encoding, torrent, 'publisher')
        # if 'created by' in torrent:
        #     info['creator'] = cls.__decode_utf8(encoding, torrent, 'created by')[:15]

        if 'info' in torrent:
            metadata = torrent['info']
        else:
            metadata = torrent

        info['name'] = cls.__decode_utf8(encoding, metadata, 'name')
        if 'files' in metadata:
            info['files'] = []
            for x in metadata['files']:
                if 'path.utf-8' in x:
                    path = cls.__decode(encoding, '/'.join(x['path.utf-8']))
                else:
                    path = cls.__decode(encoding, '/'.join(x['path']))
                if path.find('_____padding_file') < 0:
                    v = {'path': path, 'length': x['length']}
                    # if 'filehash' in x:
                    #     v['filehash'] = x['filehash'].encode('hex')
                    info['files'].append(v)
        if 'length' in metadata:
            info['length'] = metadata['length']
        else:
            info['length'] = sum([x['length'] for x in info['files']])
        # info['data_hash'] = hashlib.md5(metadata['pieces']).hexdigest()
        # if 'profiles' in metadata:
        #     info['profiles'] = metadata['profiles']
        return info

    @classmethod
    def __decode(cls, encoding, s):
        for x in (encoding, 'utf8', 'gbk', 'big5'):
            try:
                u = s.decode(x)
                return u
            except:
                pass
        return s.decode(encoding, 'ignore')

    @classmethod
    def __decode_utf8(cls, encoding, d, i):
        if i + '.utf-8' in d:
            return d[i + '.utf-8'].decode('utf8')
        return cls.__decode(encoding, d[i])
