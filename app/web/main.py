#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-05

import cron
import setting
from route import Router
from twisted.internet import defer
from twisted.internet import reactor
from protocol import BasicRequest
from protocol import BasicResource
from protocol import BasicHttpFactory
from protocol import BasicHttpProtocol
from util.tool import Util
from util.log import Logger
from util.db_mysql import DbMySql
from util.response import http_response
from util.exceptions import SystemException
from util.exceptions import NotFoundException
from util.exceptions import ForbiddenException


class ServerHttpProtocol(BasicHttpProtocol):
    def __defer_callback(self, result, request):
        if request._disconnected:
            Logger.info('<====', request.path, 'connection lost')
            return

        body, content_type = http_response(request, result)
        Logger.debug('<====', request.path, content_type)

    def __defer_errback(self, result, request):
        if request._disconnected:
            Logger.info('<====', request.path, 'connection lost')
            return
        Logger.exception()

        mo = Router.render_page({'code': 500, 'desc': 'System Error'}, 'error.html')
        body, content_type = http_response(request, mo)
        Logger.debug('<====', request.path, content_type, repr(body))

    def make_task(self, request):
        Logger.debug('====>', request.path)
        try:
            mo = Router.onMessage(request)
            if isinstance(mo, defer.Deferred):
                mo.addCallback(self.__defer_callback, request)
                mo.addErrback(self.__defer_errback, request)
                return

            if request._disconnected:
                Logger.info('<====', request.path, 'connection lost')
                return

            body, content_type = http_response(request, mo)
        except SystemException, e:
            mo = Router.render_page({'code': 500, 'desc': 'System Error'}, 'error.html')
            body, content_type = http_response(request, mo)
        except NotFoundException, e:
            mo = Router.render_page({'code': 404, 'desc': 'Not Found'}, 'error.html')
            body, content_type = http_response(request, mo)
        except ForbiddenException, e:
            mo = Router.render_page({'code': 403, 'desc': 'Forbidden Access'}, 'error.html')
            body, content_type = http_response(request, mo)
        except Exception, e:
            Logger.exception()
            mo = Router.render_page({'code': 500, 'desc': 'System Error'}, 'error.html')
            body, content_type = http_response(request, mo)
        Logger.debug('<====', request.path, content_type)


class ServerHttpFactory(BasicHttpFactory):
    protocol = ServerHttpProtocol
    requestFactory = BasicRequest

    def __init__(self, logPath=None, webroot=None):
        BasicHttpFactory.__init__(self, logPath, BasicResource(webroot))


if __name__ == "__main__":
    import os

    web_root = Util.abs_path(setting.web_root)
    Util.make_dirs(web_root)
    log_path = Util.abs_path(setting.log_path)
    log_dir = os.path.dirname(log_path)
    Util.make_dirs(log_dir)

    Logger.show_task_id(False)
    Logger.open_std_log()
    Logger.open_log(log_path)
    DbMySql.connect('dht', setting.dht_db_info)
    cron.keep_mysql_conn_alive('dht')
    DbMySql.connect('search', setting.search_db_info)
    cron.keep_mysql_conn_alive('search')
    factory = ServerHttpFactory(log_path, web_root)
    # reactor.listenTCP(setting.web_port, factory, interface='127.0.0.1')
    Logger.info("listen tcp at", setting.listen_port)
    reactor.listenTCP(setting.listen_port, factory)
    reactor.run()
