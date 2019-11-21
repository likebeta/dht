#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-27

import time
# import hashlib
import bencode


def parse(data):
    if not isinstance(data, dict):
        try:
            data = bencode.bdecode(data)
        except:
            return None, None
    info = {}
    try:
        info['create_time'] = int(data['creation date'])
    except:
        info['create_time'] = int(time.time())

    encoding = data.get('encoding', 'utf8')
    # if torrent.get('announce'):
    #     info['announce'] = __decode_utf8(encoding, torrent, 'announce')

    # if 'comment' in torrent:
    #     info['comment'] = __decode_utf8(encoding, torrent, 'comment')[:200]
    # if 'publisher-url' in torrent:
    #     info['publisher-url'] = __decode_utf8(encoding, torrent, 'publisher-url')
    # if 'publisher' in torrent:
    #     info['publisher'] = __decode_utf8(encoding, torrent, 'publisher')
    # if 'created by' in torrent:
    #     info['creator'] = __decode_utf8(encoding, torrent, 'created by')[:15]

    if 'info' in data:
        metadata = data['info']
    else:
        metadata = data

    info['name'] = __decode_utf8(encoding, metadata, 'name')
    if 'files' in metadata:
        info['files'] = []
        for x in metadata['files']:
            if 'path.utf-8' in x:
                path = __decode(encoding, '/'.join(x['path.utf-8']))
            else:
                path = __decode(encoding, '/'.join(x['path']))
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
    return info, metadata


def __decode(encoding, s):
    for x in (encoding, 'utf8', 'gbk', 'big5'):
        try:
            u = s.decode(x)
            return u
        except:
            pass
    return s.decode(encoding, 'ignore')


def __decode_utf8(encoding, d, i):
    if i + '.utf-8' in d:
        return d[i + '.utf-8'].decode('utf8')
    return __decode(encoding, d[i])
