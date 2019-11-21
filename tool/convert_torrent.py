#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-12

import os
import sys
import json
import bencode
import hashlib
from util import torrent
from util.log import Logger


def walk_dir(root, func, *args):
    for lists in os.listdir(root):
        path = os.path.join(root, lists)
        if os.path.isdir(path):
            walk_dir(path, func, *args)
        else:
            func(path, *args)


def convert_torrent(path, save_path):
    with open(path) as f:
        Logger.debug('start process', path)
        buf = f.read()
        info, metadata = torrent.parse(buf)
        if info:
            hex_hash = hashlib.sha1(bencode.bencode(metadata)).digest().encode('hex')
            with open('%s/%s' % (save_path, hex_hash), 'w') as f:
                data = json.dumps(info, separators=(',', ':'))
                f.write(data)


if __name__ == '__main__':
    torrent_path = sys.argv[1]
    save_path = sys.argv[2]
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    Logger.show_task_id(False)
    Logger.open_std_log()
    Logger.info('convert torrent to metadata from', torrent_path, 'to', save_path)
    walk_dir(torrent_path, convert_torrent, save_path)
