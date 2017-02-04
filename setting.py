#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import os

dht_db_info = {
    'db': 'dht',
    'user': 'root',
    'passwd': '359359',
    'host': '127.0.0.1',
    'port': 3306
}

search_db_info = {
    'db': '',
    'user': '',
    'passwd': '',
    'host': '127.0.0.1',
    'port': 9306
}

root_path = os.path.dirname(os.path.abspath(__file__))
log_path = os.path.dirname(root_path)

web_port = 8888
web_root = root_path + '/web/static'
web_log_path = log_path + '/log/web.log'
dht_metadata_path = log_path + '/metadata'
