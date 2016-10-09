#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-28

import sys
import bencode

with open(sys.argv[1]) as f:
    data = f.read()
    info = bencode.bdecode(data)
    print sys.argv[1], info.keys()
    if 'info' in info:
        print info['info'].keys()
