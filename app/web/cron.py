#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

from util.log import Logger
from util.db_mysql import DbMySql
from twisted.internet import task
from twisted.internet import reactor


def keep_mysql_conn_alive(alias_name):
    t = task.LoopingCall(ping, alias_name)
    reactor.callLater(60, t.start, 60)


def ping(alias_name):
    try:
        Logger.info('keep alive', alias_name)
        DbMySql.operation(alias_name, 'SELECT 1;')
    except Exception, e:
        Logger.exception('----ping exception-----')
