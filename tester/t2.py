#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2014-10-14

import json

hex_hash = 'ee35685e5ceb49f7e1450b4795912ebd53722b2a'
info_hash = hex_hash.decode('hex')

with open('%s' % hex_hash, 'r+') as f:
    data = f.read()
    print repr(data)
    info = json.loads(data)
    info['hit'] = 0
    f.truncate(0)
    f.seek(0)
    data = json.dumps(info, separators=(',', ':'))
    print repr(data)
    f.write(data)
