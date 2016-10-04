#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import os
import sys
import json
import datetime
from util.log import Logger
from util.db_mysql import DbMySql
from twisted.internet import reactor
from twisted.python.failure import Failure


def walk_dir(root, func):
    for lists in os.listdir(root):
        path = os.path.join(root, lists)
        if os.path.isdir(path):
            walk_dir(path, func)
        else:
            func(path)


def result_callback(result, sql_str, sql_arg_list):
    if isinstance(result, Failure):
        Logger.error(sql_str, sql_arg_list, result.getErrorMessage())


def inset_data(path):
    with open(path) as f:
        data = f.read()
        mt = json.loads(data)
        mt['create_time'] = datetime.datetime.fromtimestamp(mt['create_time'])
        mt['info_hash'] = os.path.basename(path)
        mt['name'] = mt['name'].encode('utf-8')
        files = mt.get('files')
        if files:
            files = json.dumps(files, separators=(',', ':'))

        sql_str = 'INSERT IGNORE INTO bt(info_hash,name,length,create_time,files) VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE hit=hit+1;'
        sql_arg_list = (mt['info_hash'], mt['name'], mt['length'], str(mt['create_time']), files)
        d = DbMySql.query('dht', sql_str, *sql_arg_list)
        d.addBoth(result_callback, sql_str, sql_arg_list)


if __name__ == '__main__':
    Logger.open_std_log()
    Logger.show_task_id(False)

    info = dict(db='dht', user='root', passwd='359359', host='127.0.0.1', port=3306)
    DbMySql.connect('dht', info)

    reactor.callWhenRunning(walk_dir, sys.argv[1], inset_data)
    reactor.run()
