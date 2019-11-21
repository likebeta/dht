#!/usr/bin/env python
# -*- coding=utf-8 -*-

# Author: likebeta <ixxoo.me@gmail.com>
# Create: 2016-10-05

import setting
from twisted.internet import defer
from twisted.internet import reactor
from util.log import Logger
from util.tool import Util
from util.response import http_response
from util.response import http_response_500
from util.response import http_response_404
from util.response import http_response_403
from util.exceptions import SystemException
from util.exceptions import NotFoundException
from util.exceptions import ForbiddenException
from util.db_mysql import DbMySql
from route import Router
from protocol import BasicRequest
from protocol import BasicResource
from protocol import BasicHttpFactory
from protocol import BasicHttpProtocol


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
        body, content_type = http_response_500(request)
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
            body, content_type = http_response_500(request)
        except NotFoundException, e:
            body, content_type = http_response_404(request)
        except ForbiddenException, e:
            body, content_type = http_response_403(request)
        except Exception, e:
            Logger.exception()
            body, content_type = http_response_500(request)
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
    DbMySql.connect('search', setting.search_db_info)
    factory = ServerHttpFactory(log_path, web_root)
    # reactor.listenTCP(setting.web_port, factory, interface='127.0.0.1')
    Logger.info("listen tcp at", setting.listen_port)
    reactor.listenTCP(setting.listen_port, factory)
    reactor.run()
