#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-28

import os
import sys
import json
import traceback


def walk_dir(root, func):
    for lists in os.listdir(root):
        path = os.path.join(root, lists)
        if os.path.isdir(path):
            walk_dir(path, func)
        else:
            func(path)


def check_file(path):
    try:
        with open(path) as f:
            data = f.read()
            json.loads(data)
    except:
        traceback.print_exc()
        print path


walk_dir(sys.argv[1], check_file)
