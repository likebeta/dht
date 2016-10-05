#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2014-10-14

import sys
import json
import time
import pymysql as mdb

search_conn = mdb.connect('127.0.0.1', '', '', '', port=9306, charset='utf8')
search_conn.ping(True)

sql = "select id, name from search where match(%s) limit %s, %s;"
search_cursor = search_conn.cursor()
search_cursor.execute(sql, (sys.argv[1], int(sys.argv[2]), int(sys.argv[3])))
items = dict(search_cursor.fetchall())
print json.dumps(items)
time.sleep(int(sys.argv[2]))
search_cursor.execute('SHOW META')
meta = dict(search_cursor.fetchall())
print json.dumps(meta)
