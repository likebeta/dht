#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import warnings
from twisted.enterprise import adbapi
from twisted.internet.defer import returnValue
from twisted.internet.defer import inlineCallbacks
from util.log import Logger

DEBUG = False


class DbMySql(object):
    def __init__(self):
        self.__CONN_MYSQL__ = {}
        warnings.filterwarnings('ignore')

    def connect(self, alias_name, info, min_pool=3, max_pool=5):
        if alias_name in self.__CONN_MYSQL__:
            return self.__CONN_MYSQL__[alias_name]

        db = str(info['db'])
        host = str(info['host'])
        port = int(info['port'])
        user = str(info['user'])
        passwd = str(info['passwd'])

        if DEBUG:
            Logger.info('DbMySql.connect->', alias_name, db, user, passwd, host, port)
        conn = adbapi.ConnectionPool('pymysql', db=db, user=user, passwd=passwd, host=host, port=port, charset='utf8',
                                     use_unicode=True, cp_reconnect=True, cp_min=min_pool, cp_max=max_pool)
        if DEBUG:
            Logger.info('DbMySql.__init__->done', conn)
        self.__CONN_MYSQL__[alias_name] = conn
        return conn

    @inlineCallbacks
    def query(self, alias_name, sql_str, *sql_arg_list):
        pool = self.__CONN_MYSQL__[alias_name]
        if DEBUG:
            Logger.debug('mysql %s: ===>' % alias_name, sql_str, sql_arg_list)
        result = yield pool.runQuery(sql_str, sql_arg_list)
        if DEBUG:
            Logger.debug('mysql %s: <===' % alias_name, sql_str, sql_arg_list, result)
        returnValue(result)

    @inlineCallbacks
    def operation(self, alias_name, sql_str, *sql_arg_list):
        pool = self.__CONN_MYSQL__[alias_name]
        if DEBUG:
            Logger.debug('mysql %s: ===>' % alias_name, sql_str, *sql_arg_list)
        result = yield pool.runOperation(sql_str, sql_arg_list)
        if DEBUG:
            Logger.debug('mysql %s: <===' % alias_name, sql_str, *sql_arg_list)
        returnValue(result)

    @inlineCallbacks
    def interaction(self, alias_name, func, *args):
        pool = self.__CONN_MYSQL__[alias_name]
        if DEBUG:
            Logger.debug('mysql %s: ===>' % alias_name, *args)
        result = yield pool.runInteraction(func, *args)
        if DEBUG:
            Logger.debug('mysql %s: <===' % alias_name, args, result)
        returnValue(result)


DbMySql = DbMySql()
