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
from twisted.internet import defer
from twisted.internet import reactor


@defer.inlineCallbacks
def walk_dir(root, func, *args):
    for lists in os.listdir(root):
        path = os.path.join(root, lists)
        if os.path.isdir(path):
            d = walk_dir(path, func, *args)
        else:
            d = func(path, *args)
        yield d


def error_callback(result, info_hash):
    Logger.error('insert error:', info_hash, result.getErrorMessage())


def read_data(path, func, *args):
    with open(path) as f:
        Logger.debug('start process', path)
        data = f.read()
        mt = json.loads(data)
        if 'create_time' in mt:
            mt['create_time'] = datetime.datetime.fromtimestamp(mt['create_time'])
        else:
            mt['create_time'] = datetime.datetime.fromtimestamp(mt['create_ts'])
        mt['info_hash'] = os.path.basename(path)
        mt['name'] = mt['name'].encode('utf-8')
        mt['hit'] = mt.get('hit', 1)
        files = mt.get('files')
        if files:
            files = json.dumps(files, separators=(',', ':'))

        sql_str = 'INSERT INTO bt1(info_hash,name,length,hit,create_time,files) VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE hit=hit+VALUES(hit);'
        sql_arg_list = (mt['info_hash'], mt['name'], mt['length'], mt['hit'], str(mt['create_time']), files)
        d = DbMySql.operation('dht', sql_str, *sql_arg_list)
        d.addErrback(error_callback, mt['info_hash'])
        return func(d, *args)


def insert_data(data, worker):
    global defer_list
    defer_list.append(data)
    if len(defer_list) >= worker:
        tmp = defer.DeferredList(defer_list, consumeErrors=True)
        defer_list = []
        return tmp


@defer.inlineCallbacks
def main(path, worker=5):
    yield walk_dir(path, read_data, insert_data, worker)
    global defer_list
    if defer_list:
        yield defer.DeferredList(defer_list, consumeErrors=True)
        defer_list = []
    reactor.stop()


if __name__ == '__main__':
    Logger.open_std_log()
    Logger.show_task_id(False)

    info = dict(db='dht', user='root', passwd='359359', host='127.0.0.1', port=3306)
    DbMySql.connect('dht', info, 5, 20)
    defer_list = []
    reactor.callWhenRunning(main, sys.argv[1], int(sys.argv[2]))
    reactor.run()
