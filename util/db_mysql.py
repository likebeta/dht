#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

import warnings
from twisted.enterprise import adbapi
from twisted.internet.defer import returnValue
from twisted.internet.defer import inlineCallbacks
from util.log import Logger


class DbMySql(object):
    def __init__(self):
        self.__CONN_MYSQL__ = {}
        warnings.filterwarnings('ignore')

    def connect(self, alias_name, *args):
        if alias_name in self.__CONN_MYSQL__:
            return self.__CONN_MYSQL__[alias_name]

        if len(args) == 1:
            confDict = args[0]
            db = str(confDict['db'])
            host = str(confDict['host'])
            port = int(confDict['port'])
            user = str(confDict['user'])
            passwd = str(confDict['passwd'])
        elif len(args) == 5:
            db = str(args[0])
            host = str(args[1])
            port = int(args[2])
            user = str(args[3])
            passwd = str(args[4])
        else:
            raise Exception('error args')

        Logger.debug('DbMySql.connect->', alias_name, db, user, passwd, host, port)
        conn = adbapi.ConnectionPool('pymysql', db=db, user=user, passwd=passwd, host=host, port=port, charset='utf8',
                                     use_unicode=True, cp_reconnect=True)
        Logger.debug('DbMySql.__init__->done', conn)
        self.__CONN_MYSQL__[alias_name] = conn
        return conn

    @inlineCallbacks
    def query(self, alias_name, sql_str, *sql_arg_list):
        pool = self.__CONN_MYSQL__[alias_name]
        Logger.debug('mysql %s: ===>' % alias_name, sql_str, sql_arg_list)
        result = yield pool.runQuery(sql_str, sql_arg_list)
        Logger.debug('mysql %s: <===' % alias_name, sql_str, sql_arg_list, result)
        returnValue(result)

    @inlineCallbacks
    def operation(self, alias_name, sql_str, *sql_arg_list):
        pool = self.__CONN_MYSQL__[alias_name]
        Logger.debug('mysql %s: ===>' % alias_name, sql_str, *sql_arg_list)
        result = yield pool.runOperation(sql_str, sql_arg_list)
        Logger.debug('mysql %s: <===' % alias_name, sql_str, *sql_arg_list)
        returnValue(result)

    @inlineCallbacks
    def interaction(self, alias_name, func, *args):
        pool = self.__CONN_MYSQL__[alias_name]
        Logger.debug('mysql %s: ===>' % alias_name, *args)
        result = yield pool.runInteraction(func, *args)
        Logger.debug('mysql %s: <===' % alias_name, args, result)
        returnValue(result)


DbMySql = DbMySql()
