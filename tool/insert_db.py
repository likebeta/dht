#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import os
import sys
import json
import datetime
from util.txmysql import client
from util.log import Logger
from twisted.internet import task
from twisted.internet import defer
from twisted.internet import reactor


def walk_dir(root, func):
    for lists in os.listdir(root):
        path = os.path.join(root, lists)
        if os.path.isfile(path):
            # Logger.info(path, '=====>')
            yield func(path)
            # Logger.info(path, '<=====')
        else:
            for _ in walk_dir(path, func):
                yield _


def error_callback(result, info_hash):
    Logger.error('insert error:', info_hash)


def read_data(path):
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

        sql_str = 'INSERT INTO bt(info_hash,name,length,hit,create_time,files) VALUES(%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE hit=hit+VALUES(hit);'
        sql_arg_list = (mt['info_hash'], mt['name'], mt['length'], mt['hit'], str(mt['create_time']), files)
        conn = get_conn()
        d = conn.runOperation(sql_str, sql_arg_list)
        d.addErrback(error_callback, mt['info_hash'])
        d.addBoth(lambda ign: release_conn(conn))
        return d


@defer.inlineCallbacks
def main(path, worker=5):
    coop = task.Cooperator()
    work_iter = walk_dir(path, read_data)
    defer_list = []
    for i in xrange(worker):
        d = coop.coiterate(work_iter)
        defer_list.append(d)
    yield defer.DeferredList(defer_list, consumeErrors=True)
    Logger.info('work done')
    reactor.stop()


def init_conn(max_conn):
    conn_list = set()
    for _ in range(max_conn):
        conn = client.MySQLConnection(**info)
        conn_list.add(conn)
    return conn_list


def get_conn():
    return conn_list.pop()


def release_conn(conn):
    conn_list.add(conn)


if __name__ == '__main__':
    Logger.open_std_log()
    Logger.show_task_id(False)
    max_conn = int(sys.argv[2])
    # client.DEBUG = True

    info = {
        'hostname': '127.0.0.1',
        'username': 'root',
        'password': '359359',
        'database': 'dht',
        'connect_timeout': 3,
        'retry_on_error': True,
        'port': 3306,
    }
    conn_list = init_conn(max_conn)
    reactor.callWhenRunning(main, sys.argv[1], max_conn)
    reactor.run()
