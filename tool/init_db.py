#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-09-02

from util.log import Logger
from util.db_mysql import DbMySql
from twisted.internet import defer
from twisted.internet import reactor
from twisted.python.failure import Failure


@defer.inlineCallbacks
def main():
    sql_str_list = (
        "CREATE DATABASE IF NOT EXISTS dht DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;",
        "use dht;",
        "CREATE TABLE IF NOT EXISTS `bt`(" +
        "`id` INT(4) unsigned NOT NULL PRIMARY KEY auto_increment," +
        "`info_hash` CHAR(40) NOT NULL unique," +
        "`create_time` DATETIME NOT NULL," +
        "`name` VARCHAR(255) NOT NULL," +
        "`hit` BIGINT(8) NOT NULL DEFAULT '1'," +
        "`access_ts` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP," +
        "`length` BIGINT(8) NOT NULL DEFAULT '0'," +
        "`files` TEXT DEFAULT NULL)" +
        "DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;"
    )
    try:
        for sql_str in sql_str_list:
            result = yield DbMySql.operation('dht', sql_str)
            if isinstance(result, Failure):
                Logger.debug(sql_str, result.getErrorMessage())
                break
    except Exception, e:
        Logger.error(e)
    reactor.stop()


if __name__ == '__main__':
    Logger.open_std_log()
    Logger.show_task_id(False)

    info = dict(db='', user='root', passwd='359359', host='127.0.0.1', port=3306)
    DbMySql.connect('dht', info)

    reactor.callWhenRunning(main)
    reactor.run()
