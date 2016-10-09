#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2014-10-14

import sys
import pymysql as mdb

dst_conn = mdb.connect('127.0.0.1', '', '', '', port=9306, charset='utf8')
dst_curr = dst_conn.cursor()
dst_curr.execute('SET NAMES utf8')

sql = 'SELECT id, name FROM search WHERE id=%s limit 1;'
dst_curr.execute(sql, (int(sys.argv[1]),))
result = [list(one) for one in dst_curr.fetchall()]
dst_curr.execute('SHOW META')
tmp = dict(dst_curr.fetchall())

print result
print
print tmp

